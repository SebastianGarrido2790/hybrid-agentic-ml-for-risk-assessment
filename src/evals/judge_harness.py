"""
LLM-as-a-Judge Evaluation Harness for ACRAS.

This module implements the qualitative evaluation layer that sits above the
deterministic unit test pyramid. It orchestrates two sequential LLM calls:

1. **ACRAS Agent Call** — invokes the LangGraph relay to produce a credit report.
2. **Judge Call** — submits the report to a second LLM (acting as an impartial
   evaluator) that scores the output on four axes: Relevance, Faithfulness,
   Tool Usage, and Business Value Alignment.

Architecture Note (Brain vs. Brawn):
    The Judge LLM is the Brain: it reasons about quality.
    The ``_check_thresholds()`` helper is the Brawn: it applies deterministic
    pass/fail logic using the Pydantic-validated ``JudgeVerdict`` schema.

Usage:
    Run via the ``scripts/run_evals.py`` CLI runner, or integrate into CI
    with ``pytest -m eval``.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.model_factory import get_llm
from src.agents.prompt_loader import get_prompt
from src.evals.schemas import (
    DimensionScore,
    EvalResult,
    EvalSuiteReport,
    GoldenSample,
    JudgeVerdict,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
DATASET_VERSION = "1.0.0"

# Dimension thresholds
_THRESHOLDS: dict[str, int] = {
    "relevance": 4,
    "faithfulness": 4,
    "tool_usage": 4,
    "business_value": 3,
}


# ---------------------------------------------------------------------------
# Golden Dataset Loader
# ---------------------------------------------------------------------------


def load_golden_dataset(path: Path = GOLDEN_DATASET_PATH) -> list[GoldenSample]:
    """Load and validate the golden evaluation dataset.

    Args:
        path: Absolute path to ``golden_dataset.json``.

    Returns:
        A validated list of ``GoldenSample`` objects.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        ValueError: If any sample fails Pydantic schema validation.
    """
    if not path.exists():
        raise FileNotFoundError(f"Golden dataset not found at: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    samples: list[GoldenSample] = []
    for item in raw["samples"]:
        samples.append(GoldenSample(**item))

    logger.info(f"Loaded {len(samples)} golden samples from {path.name}")
    return samples


# ---------------------------------------------------------------------------
# Agent Invocation (ACRAS Brain)
# ---------------------------------------------------------------------------


def _invoke_acras_agent(sample: GoldenSample) -> str:
    """Invoke the ACRAS LangGraph relay for a single golden sample.

    This function imports the compiled LangGraph ``app`` at call time to avoid
    circular imports at module load. The agent runs fully end-to-end, including
    tool calls, fallback logic, and deterministic guardrail injection.

    Args:
        sample: The ``GoldenSample`` whose ``input_query`` will be sent to
            the agent.

    Returns:
        The raw text content of the final agent message (the credit report).

    Raises:
        RuntimeError: If the agent graph returns no messages.
    """
    # Import at call-time to avoid circular import at module load
    from src.agents.graph import app  # type: ignore[import]

    state_input = {
        "messages": [HumanMessage(content=sample.input_query)],
        "company_id": str(sample.company_id),
    }
    # type: ignore[arg-type] — LangGraph compiled app accepts AgentState-compatible
    # dicts at runtime; pyright cannot resolve the TypedDict match across the
    # dynamic import boundary (known LangGraph/pyright limitation, whitelisted per ruleset).
    result: dict[str, Any] = app.invoke(state_input)  # type: ignore[arg-type]

    messages = result.get("messages", [])
    if not messages:
        raise RuntimeError(f"Agent returned no messages for sample {sample.sample_id}")

    # The last message might be from the 'monitor' node (SystemMessage).
    # We need the last AIMessage, which is the CRO's final report.
    for m in reversed(messages):
        # Skip system messages from the monitor node
        if isinstance(m, SystemMessage) and "[MONITOR]" in str(m.content):
            continue
        # Skip other system messages or tool messages to find the final report
        if hasattr(m, "content") and str(m.content).strip():
            return str(m.content)

    raise RuntimeError(
        f"Could not find a valid report in messages for sample {sample.sample_id}"
    )


# ---------------------------------------------------------------------------
# Judge LLM Invocation (Impartial Evaluator)
# ---------------------------------------------------------------------------


def _build_judge_user_prompt(sample: GoldenSample, agent_response: str) -> str:
    """Build the structured user-turn message for the judge LLM.

    Injects the ground truth context alongside the agent's report so the judge
    can verify faithfulness against the expected financial ratios.

    Args:
        sample: The golden sample providing ground truth context.
        agent_response: The credit report text produced by the ACRAS agent.

    Returns:
        A formatted multi-section string ready to be sent as a ``HumanMessage``.
    """
    ratios_str = "\n".join(
        f"  - {k}: {v}" for k, v in sample.ground_truth_ratios.items()
    )
    keywords_str = ", ".join(f'"{kw}"' for kw in sample.expected_keywords)

    return (
        "## Evaluation Request\n\n"
        f"**Scenario:** {sample.scenario_description}\n"
        f"**User Query:** {sample.input_query}\n\n"
        "## Ground Truth Context\n"
        f"**Expected Recommendation:** {sample.expected_recommendation}\n"
        f"**Expected Risk Tier:** {sample.expected_risk_tier}\n"
        f"**Expected Keywords:** {keywords_str}\n"
        f"**Ground Truth Financial Ratios:**\n{ratios_str}\n\n"
        "## Agent Response to Evaluate\n"
        f"{agent_response}\n\n"
        "## Instructions\n"
        "Score the Agent Response above against all four axes. "
        "Return ONLY the JSON object — no markdown fences, no prose outside the JSON."
    )


def _parse_judge_response(raw: str) -> JudgeVerdict:
    """Extract and validate the JSON verdict from the judge LLM's raw response.

    Applies a regex strip to tolerate models that wrap JSON in markdown code
    fences despite instructions, then validates via Pydantic.

    Args:
        raw: The raw string response from the judge LLM.

    Returns:
        A validated ``JudgeVerdict`` instance.

    Raises:
        ValueError: If JSON parsing or Pydantic validation fails.
    """
    # Strip markdown fences if the model added them despite instructions
    cleaned = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE).strip()
    cleaned = cleaned.rstrip("`").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Judge response is not valid JSON: {e}\nRaw: {raw[:500]}"
        ) from e

    # Inject pass_threshold into each dimension if the LLM omitted it
    for dim, threshold in _THRESHOLDS.items():
        if dim in data and "pass_threshold" not in data[dim]:
            data[dim]["pass_threshold"] = threshold

    return JudgeVerdict(**data)


def _invoke_judge(sample: GoldenSample, agent_response: str) -> JudgeVerdict:
    """Invoke the LLM Judge to score a single agent response.

    Uses the primary Gemini model (no tool binding). The judge prompt is loaded
    from the versioned external file ``llm_judge_v1.txt`` following No "Naked" Prompts.

    Args:
        sample: The golden sample providing the ground truth evaluation context.
        agent_response: The credit report text to be scored.

    Returns:
        A validated ``JudgeVerdict`` instance.

    Raises:
        RuntimeError: If the judge model invocation fails.
        ValueError: If the response cannot be parsed into a ``JudgeVerdict``.
    """
    system_prompt = get_prompt("system_prompts", "llm_judge_v1.txt")
    user_message = _build_judge_user_prompt(sample, agent_response)

    # Use the Gemini flash model as the judge (no tools needed)
    if not os.environ.get("GOOGLE_API_KEY"):
        raise RuntimeError(
            "GOOGLE_API_KEY missing from environment. Evaluation suite requires an API key."
        )

    try:
        judge_model = get_llm(provider="gemini")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize judge LLM: {e}") from e

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    try:
        response = judge_model.invoke(messages)
        raw_content = str(response.content)
        if isinstance(response.content, list):
            raw_content = " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in response.content
            )
    except Exception as e:
        raise RuntimeError(f"Judge LLM invocation failed: {e}") from e

    return _parse_judge_response(raw_content)


# ---------------------------------------------------------------------------
# Threshold Gate (Deterministic Brawn)
# ---------------------------------------------------------------------------


def _check_thresholds(verdict: JudgeVerdict) -> bool:
    """Apply deterministic pass/fail logic against the thresholds.

    This function is the Brawn of the eval pipeline: given a structured
    ``JudgeVerdict``, it applies simple integer comparisons — no LLM reasoning.

    Args:
        verdict: The validated ``JudgeVerdict`` from the judge LLM.

    Returns:
        True if ALL four dimension scores meet or exceed their thresholds.
    """
    dimensions: dict[str, DimensionScore] = {
        "relevance": verdict.relevance,
        "faithfulness": verdict.faithfulness,
        "tool_usage": verdict.tool_usage,
        "business_value": verdict.business_value,
    }
    all_passed = True
    for dim_name, dim_score in dimensions.items():
        passed = dim_score.score >= dim_score.pass_threshold
        status = "PASS" if passed else "FAIL"
        logger.info(
            f"  [{status}] {dim_name}: {dim_score.score}/{dim_score.pass_threshold} "
            f"— {dim_score.justification}"
        )
        if not passed:
            all_passed = False
    return all_passed


# ---------------------------------------------------------------------------
# Single-Sample Evaluator
# ---------------------------------------------------------------------------


def evaluate_sample(sample: GoldenSample, dry_run: bool = False) -> EvalResult:
    """Run a full end-to-end evaluation for a single golden sample.

    Orchestrates two steps:
    1. Invokes the ACRAS agent to generate a credit report.
    2. Submits the report to the LLM Judge for structured scoring.

    Args:
        sample: The golden sample to evaluate.
        dry_run: If True, skips LLM calls and returns a synthetic result.
            Useful for testing the harness pipeline without API costs.

    Returns:
        A fully populated ``EvalResult``, including ``judge_verdict`` and
        the deterministic ``passed`` flag.
    """
    logger.info(f"--- Evaluating {sample.sample_id} (Company {sample.company_id}) ---")

    if dry_run:
        logger.info("  [DRY RUN] Returning synthetic EvalResult.")
        synthetic_verdict = JudgeVerdict(
            relevance=DimensionScore(
                score=4, justification="Dry run placeholder.", pass_threshold=4
            ),
            faithfulness=DimensionScore(
                score=4, justification="Dry run placeholder.", pass_threshold=4
            ),
            tool_usage=DimensionScore(
                score=4, justification="Dry run placeholder.", pass_threshold=4
            ),
            business_value=DimensionScore(
                score=3, justification="Dry run placeholder.", pass_threshold=3
            ),
            overall_summary="Dry run: all dimensions at threshold.",
        )
        return EvalResult(
            sample_id=sample.sample_id,
            company_id=sample.company_id,
            agent_response="[DRY RUN — no agent call made]",
            judge_verdict=synthetic_verdict,
            passed=True,
            eval_timestamp=datetime.utcnow(),
        )

    # Step 1: Run the ACRAS agent
    try:
        agent_response = _invoke_acras_agent(sample)
        logger.info(f"  Agent response received ({len(agent_response)} chars).")
    except Exception as e:
        logger.error(f"  Agent invocation failed: {e}")
        return EvalResult(
            sample_id=sample.sample_id,
            company_id=sample.company_id,
            agent_response="",
            passed=False,
            error=f"Agent error: {e}",
            eval_timestamp=datetime.utcnow(),
        )

    # Step 2: Run the LLM Judge
    try:
        verdict = _invoke_judge(sample, agent_response)
        passed = _check_thresholds(verdict)
        logger.info(f"  Overall: {'PASSED' if passed else 'FAILED'}")
    except Exception as e:
        logger.error(f"  Judge invocation failed: {e}")
        return EvalResult(
            sample_id=sample.sample_id,
            company_id=sample.company_id,
            agent_response=agent_response,
            passed=False,
            error=f"Judge error: {e}",
            eval_timestamp=datetime.utcnow(),
        )

    return EvalResult(
        sample_id=sample.sample_id,
        company_id=sample.company_id,
        agent_response=agent_response,
        judge_verdict=verdict,
        passed=passed,
        eval_timestamp=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Suite Runner
# ---------------------------------------------------------------------------


def run_eval_suite(
    samples: list[GoldenSample] | None = None,
    dry_run: bool = False,
) -> EvalSuiteReport:
    """Run the full evaluation suite against the golden dataset.

    Iterates through all samples, collects ``EvalResult`` objects, and
    aggregates them into an ``EvalSuiteReport`` with mean scores and pass rate.

    Args:
        samples: Optional subset of samples to evaluate. If None, loads the
            full golden dataset from ``golden_dataset.json``.
        dry_run: If True, bypasses all LLM calls for pipeline testing.

    Returns:
        A fully populated ``EvalSuiteReport`` ready for logging or persistence.
    """
    if samples is None:
        samples = load_golden_dataset()

    results: list[EvalResult] = []
    for sample in samples:
        result = evaluate_sample(sample, dry_run=dry_run)
        results.append(result)

    # Aggregate scores
    scored = [r for r in results if r.judge_verdict is not None]
    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count

    def _mean(attr: str) -> float:
        if not scored:
            return 0.0
        return sum(getattr(r.judge_verdict, attr).score for r in scored) / len(scored)  # type: ignore[union-attr]

    report = EvalSuiteReport(
        suite_version=DATASET_VERSION,
        run_timestamp=datetime.utcnow(),
        total_samples=len(results),
        passed_samples=passed_count,
        failed_samples=failed_count,
        pass_rate=passed_count / len(results) if results else 0.0,
        mean_relevance=_mean("relevance"),
        mean_faithfulness=_mean("faithfulness"),
        mean_tool_usage=_mean("tool_usage"),
        mean_business_value=_mean("business_value"),
        results=results,
    )

    logger.info(
        f"Suite complete: {passed_count}/{len(results)} passed "
        f"({report.pass_rate:.1%}) | "
        f"Relevance={report.mean_relevance:.2f} "
        f"Faithfulness={report.mean_faithfulness:.2f} "
        f"ToolUsage={report.mean_tool_usage:.2f} "
        f"BizValue={report.mean_business_value:.2f}"
    )
    return report
