"""
Live Performance Monitoring for ACRAS.

This module provides utilities to score agent performance on live requests
using the LLM-as-a-Judge pattern, logging results to MLflow and OTel.
"""

import os
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from opentelemetry import trace

from src.agents.model_factory import get_llm
from src.agents.prompt_loader import get_prompt
from src.evals.schemas import JudgeVerdict
from src.utils.logger import get_logger

logger = get_logger(__name__)
tracer = trace.get_tracer("acras.monitoring")

# Dimension thresholds (reused from judge_harness)
_THRESHOLDS: dict[str, int] = {
    "relevance": 4,
    "faithfulness": 4,
    "tool_usage": 4,
    "business_value": 3,
}


def log_live_performance(
    input_query: str, agent_response: str, context_data: str, company_id: str
) -> dict[str, Any]:
    """
    Score a live agent response using the LLM-as-a-Judge and log to observability backends.

    Args:
        input_query: The original user query.
        agent_response: The final report produced by the orchestrator.
        context_data: The raw data retrieved by tools during the session.
        company_id: The ID of the company being assessed.

    Returns:
        A dictionary containing the scores and justifications.
    """
    if os.environ.get("SKIP_LIVE_MONITORING"):
        return {"status": "skipped"}

    with tracer.start_as_current_span("live_monitoring_judge") as span:
        span.set_attribute("acras.company_id", company_id)

        try:
            # 1. Build Judge Prompt
            system_prompt = get_prompt("system_prompts", "llm_judge_v1.txt")

            user_prompt = (
                "## Live Monitoring Request\n\n"
                f"**User Query:** {input_query}\n"
                f"**Company ID:** {company_id}\n\n"
                "## Context Data (Retrieved by Tools)\n"
                f"{context_data}\n\n"
                "## Agent Response to Evaluate\n"
                f"{agent_response}\n\n"
                "## Instructions\n"
                "Score this live response. Since this is NOT a golden sample, "
                "judge faithfulness against the 'Context Data' provided above. "
                "Return ONLY the JSON object."
            )

            # 2. Invoke Judge
            judge_model = get_llm(provider="gemini")
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = judge_model.invoke(messages)
            raw_content = str(response.content)

            # 3. Parse Verdict
            from src.evals.judge_harness import _parse_judge_response

            verdict = _parse_judge_response(raw_content)

            # 4. Log to MLflow if available
            _log_to_mlflow(verdict, company_id)

            # 5. Set Span Attributes
            span.set_attribute("acras.eval.relevance", verdict.relevance.score)
            span.set_attribute("acras.eval.faithfulness", verdict.faithfulness.score)
            span.set_attribute("acras.eval.tool_usage", verdict.tool_usage.score)
            span.set_attribute(
                "acras.eval.business_value", verdict.business_value.score
            )

            logger.info(
                f"Live monitoring complete for Company {company_id}. "
                f"Scores: R={verdict.relevance.score}, F={verdict.faithfulness.score}"
            )

            return verdict.model_dump()

        except Exception as e:
            logger.error(f"Live monitoring failed: {e}")
            span.record_exception(e)
            return {"status": "error", "error": str(e)}


def _log_to_mlflow(verdict: JudgeVerdict, company_id: str) -> None:
    """Log live evaluation results to MLflow."""
    try:
        import mlflow

        # We assume an active run if called within a pipeline,
        # or we start a nested/new run for monitoring.
        run = mlflow.active_run()
        if not run:
            # If no active run, we might be in a standalone API call.
            # We don't want to start a new MLflow run for every single API call
            # as it creates too much noise.
            # Instead, we should probably log to a dedicated "Live Monitoring" experiment.
            mlflow.set_experiment("acras_live_monitoring")
            with mlflow.start_run(
                run_name=f"monitor_{company_id}_{datetime.now().strftime('%H%M%S')}"
            ):
                mlflow.log_metrics(
                    {
                        "live/relevance": verdict.relevance.score,
                        "live/faithfulness": verdict.faithfulness.score,
                        "live/tool_usage": verdict.tool_usage.score,
                        "live/business_value": verdict.business_value.score,
                    }
                )
        else:
            # Log as part of the current run
            mlflow.log_metrics(
                {
                    f"live/{company_id}/relevance": verdict.relevance.score,
                    f"live/{company_id}/faithfulness": verdict.faithfulness.score,
                }
            )
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"MLflow monitoring log failed: {e}")
