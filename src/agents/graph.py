"""
Multi-Agent Orchestrator for ACRAS.

This module implements a "Relay Team" pattern where specialized agents pass
the task context to each other:
1. Financial Analyst: Fetches data and calculates ratios.
2. Data Scientist: Predicts default probability using the ML API.
3. Orchestrator (CRO): Synthesizes the final report.

The architecture incorporates hot-swapping logic via dynamic imports,
configuration factories, and OpenTelemetry tracing for agent calls
using gen_ai.* semantic conventions.
"""

import importlib
import operator
import re
from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from opentelemetry import trace

from src.agents.monitoring import log_live_performance
from src.agents.tools.finance_tool import (
    calculate_current_ratio,
    calculate_debt_to_equity,
    calculate_ebitda_margin,
    calculate_revenue_growth,
)
from src.agents.tools.lookup_tool import fetch_company_data
from src.agents.tools.ml_api_tool import get_credit_risk_score
from src.config.configuration import ConfigurationManager
from src.utils.logger import get_logger


# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    company_id: str  # Context passed along


# --- Tool Sets ---
logger = get_logger(__name__)
financial_tools_list = [
    fetch_company_data,
    calculate_debt_to_equity,
    calculate_ebitda_margin,
    calculate_current_ratio,
    calculate_revenue_growth,
]
ml_tools_list = [
    get_credit_risk_score,
]


def get_dynamic_models(
    tools_list: list[Any] | None = None, tool_choice: str | None = None
):
    """
    Dynamically instantiates the model hierarchy based on current config.py.
    This allows for hot-swapping providers without restarting the app.
    """
    # Force refresh of config and settings
    import src.agents.config as config_module

    importlib.reload(config_module)  # Requires a "module object" to work
    current_settings = config_module.get_agent_settings()

    # Force refresh of model factory
    import src.agents.model_factory as factory_module

    importlib.reload(factory_module)  # Requires a "module object" to work

    # 1. Primary
    try:
        m_primary = factory_module.get_llm()
    except Exception as e:
        logger.warning(f"Primary model initialization failed: {e}")
        m_primary = None

    # 2. Fallback 1 (Dynamic switch)
    try:
        if current_settings.DEFAULT_LLM_PROVIDER == "huggingface":
            m_fb1 = factory_module.get_llm(
                provider="gemini", model_name=current_settings.GEMINI_POWER_MODEL
            )
        else:
            m_fb1 = factory_module.get_llm(provider="huggingface")
    except Exception as e:
        logger.warning(f"Fallback-1 model initialization failed: {e}")
        m_fb1 = None

    # 3. Fallback 2 (Lite)
    try:
        m_fb2 = factory_module.get_llm(
            provider="gemini", model_name=current_settings.GEMINI_LITE_MODEL
        )
    except Exception as e:
        logger.warning(f"Fallback-2 model initialization failed: {e}")
        m_fb2 = None

    raw_models = [m_primary, m_fb1, m_fb2]

    if tools_list:
        return bind_tools_to_all(
            tools_list, fallback_models=raw_models, tool_choice=tool_choice
        )
    return raw_models


def bind_tools_to_all(
    tools: list[Any], fallback_models: list[Any], tool_choice: str | None = None
):
    """Refactored helper for dynamic binding"""
    bound = []
    for m in fallback_models:
        if not m:
            bound.append(None)
            continue

        try:
            # Attempt binding with tool_choice if provided
            if tool_choice:
                bound.append(m.bind_tools(tools, tool_choice=tool_choice))
            else:
                bound.append(m.bind_tools(tools))
        except Exception as e:
            logger.warning(f"Model {m} failed tool binding (choice={tool_choice}): {e}")
            try:
                # Fallback to simple binding without tool_choice
                logger.info(f"Retrying binding for {m} without tool_choice...")
                bound.append(m.bind_tools(tools))
            except Exception as e2:
                logger.error(f"Critical failure binding tools to {m}: {e2}")
                bound.append(m)
    return bound


# --- Helper for Fallback ---
def invoke_with_fallback(
    models_tier: list[Any], inputs: list[BaseMessage], agent_name: str = "Agent"
) -> tuple[BaseMessage, list[BaseMessage]]:
    """
    Sequentially attempts to invoke models in the provided list (Tiers).
    Returns (response_message, log_messages_list).
    """
    logs = []
    state_errors = []

    for i, model in enumerate(models_tier):
        if not model:
            continue

        # Robust model name detection
        if hasattr(model, "model_name"):
            model_info = str(model.model_name).lower()
        elif hasattr(model, "model"):
            model_info = str(model.model).lower()
        elif hasattr(model, "llm") and hasattr(model.llm, "repo_id"):
            model_info = str(model.llm.repo_id).lower()
        else:
            model_info = str(getattr(model, "repo_id", "Unknown")).lower()

        tier_name = ["Primary", "1st Fallback", "2nd Fallback"][i]

        try:
            # OPTIMIZATION: If it's the 1st/2nd fallback, merge instructions into the prompt.
            # Do NOT merge if i == 0, as it destroys the strict formatting ChatHuggingFace needs for tool calls
            if i > 0:
                system_instruction = ""
                user_messages = []
                for m in inputs:
                    if isinstance(m, SystemMessage):
                        system_instruction += f"{m.content}\n\n"
                    else:
                        user_messages.append(m)

                if user_messages:
                    last_msg = user_messages[-1]
                    # Ensure the model cannot ignore the report structure
                    new_content = (
                        "### ROLE & GUIDELINES ###\n"
                        f"{system_instruction}\n"
                        "### PREVIOUS CONTEXT (DO NOT REPEAT THIS) ###\n"
                        f"{last_msg.content or ''}\n\n"
                        "### YOUR TASK ###\n"
                        "Provide ONLY your specific analysis. Do NOT repeat or output the previous context.\n"
                        "RESPONSE STRUCTURE: Follow mandatory sections strictly."
                    )
                    new_last_msg = HumanMessage(content=new_content)
                    final_inputs = user_messages[:-1] + [new_last_msg]
                else:
                    final_inputs = [HumanMessage(content=system_instruction)]
            else:
                final_inputs = inputs

            with trace.get_tracer("acras").start_as_current_span("llm_call") as span:
                span.set_attribute("gen_ai.system", model_info)
                span.set_attribute("gen_ai.agent.name", agent_name)
                span.set_attribute("gen_ai.request.tier", tier_name)
                response = model.invoke(final_inputs)

            # Normalize Gemini's output where it returns list of dicts for message content.
            # This is essential to prevent breaking the concatenation in downstream agents.
            if isinstance(response.content, list):
                text_parts = []
                for part in response.content:
                    if isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                    elif isinstance(part, str):
                        text_parts.append(part)
                response.content = "".join(text_parts)

            logger.info(f"🤖 {agent_name} -> Calling {tier_name} ({model_info})...")
            if i > 0:
                logs.append(
                    SystemMessage(
                        content=f"🔄 Falling back to {tier_name} ({model_info})..."
                    )
                )

            return response, logs

        except Exception as e:
            error_msg = f"Tier {i + 1} ({tier_name} - {model_info}) failed: {str(e)}"
            # Safe print for Windows terminal (cp1252)
            logger.warning(f"! {agent_name}: {error_msg}")
            # Keep emoji for Streamlit UI parsing
            logs.append(SystemMessage(content=f"⚠️ {tier_name} ({model_info}) failed."))
            state_errors.append(error_msg)

            if i == len(models_tier) - 1:
                combined_errors = "\n".join(state_errors)
                return SystemMessage(
                    content=f"Error: All tiers failed.\n{combined_errors}"
                ), logs

    return SystemMessage(content="System Error: No models available."), logs


# --- Nodes ---


def financial_analyst_node(state: AgentState):
    """
    Agent 1: Senior Financial Analyst.
    Focus: Data extraction and metric calculation.
    """
    messages = state["messages"]

    # DYNAMIC RELOAD for HOT SWAPPING
    import src.agents.prompts as prompts_module

    importlib.reload(prompts_module)  # Requires a "module object" to work
    system_prompt = getattr(prompts_module, "FINANCIAL_ANALYST_SYSTEM_PROMPT")

    models = get_dynamic_models(financial_tools_list)
    inputs = [SystemMessage(content=system_prompt)] + messages
    response, logs = invoke_with_fallback(models, inputs, "Financial Analyst")
    return {"messages": logs + [response]}


def data_scientist_node(state: AgentState):
    """
    Agent 2: Risk Data Scientist.
    Focus: Quantitative ML risk prediction.
    """
    messages = state["messages"]

    # DYNAMIC RELOAD for HOT SWAPPING
    import src.agents.prompts as prompts_module

    importlib.reload(prompts_module)  # Requires a "module object" to work
    system_prompt = getattr(prompts_module, "DATA_SCIENTIST_SYSTEM_PROMPT")

    # Inject Company ID to ensure the agent doesn't hallucinate or forget to call the tool
    company_id = state.get("company_id", "Unknown")
    system_prompt += f"\n\nTARGET COMPANY ID: {company_id}"

    # Force tool usage if it hasn't been called yet.
    # Check if there's any ToolMessage indicating ml_tools ran, or just any ToolMessage AFTER financial analyst
    has_called_ml = any(
        hasattr(m, "name") and m.name == "get_credit_risk_score" for m in messages
    )

    # In langchain-google-genai, "any" forces the model to call one of the provided tools
    current_tool_choice = "any" if not has_called_ml else None

    models = get_dynamic_models(ml_tools_list, tool_choice=current_tool_choice)
    inputs = [SystemMessage(content=system_prompt)] + messages
    response, logs = invoke_with_fallback(models, inputs, "Data Scientist")
    return {"messages": logs + [response]}


def orchestrator_node(state: AgentState):
    """
    Agent 3: CRO / Orchestrator.
    Focus: Synthesis and final directive.
    """
    messages = state["messages"]

    # DYNAMIC RELOAD for HOT SWAPPING
    import src.agents.prompts as prompts_module

    importlib.reload(prompts_module)
    system_prompt = getattr(prompts_module, "ORCHESTRATOR_SYSTEM_PROMPT")

    # PREVENT TRUNCATION & REDUNDANCY:
    # 1. Extract Specialist findings
    analyst_finding = ""
    scientist_finding = ""

    for m in reversed(messages):
        content = str(m.content)
        # Lenient matching for specialist reports
        if (
            "Summary Opinion" in content or "Financial Analyst" in content
        ) and not analyst_finding:
            analyst_finding = content
        if (
            "Quantitative Risk Analysis" in content or "Data Scientist" in content
        ) and not scientist_finding:
            scientist_finding = content

    else:
        context_fallback = f"--- ANALYST ---\n{analyst_finding}\n\n--- SCIENTIST ---\n{scientist_finding}"

    # --- DETERMINISTIC GUARDRAILS (R-01) ---
    guardrails = []
    try:
        # Look for raw data message to extract critical ratios
        for msg in messages:
            if hasattr(msg, "content") and "'ratio_mora'" in str(msg.content):
                # Clean up the string to make it parseable if it's formatted as a dict string
                data_str = str(msg.content)
                # Basic extraction of floats from the string using regex if needed,
                # or just look for the key-value pairs.
                mora_match = re.search(r"'ratio_mora':\s*([0-9.]+)", data_str)
                liq_match = re.search(r"'current_ratio':\s*([0-9.]+)", data_str)

                config_mgr = ConfigurationManager()
                risk_params = config_mgr.get_risk_params_config()

                if mora_match:
                    mora_val = float(mora_match.group(1))
                    if mora_val > risk_params.mora_critical:
                        guardrails.append(
                            f"- [CRITICAL] Mora Ratio is {mora_val * 100:.1f}%. Threshold for HIGH risk is {risk_params.mora_critical * 100:.0f}%."
                        )
                if liq_match:
                    liq_val = float(liq_match.group(1))
                    if liq_val < risk_params.current_ratio_critical:
                        guardrails.append(
                            f"- [CRITICAL] Current Ratio is {liq_val:.2f}. Threshold for HIGH risk is {risk_params.current_ratio_critical:.2f}."
                        )
                break
    except Exception as e:
        logger.warning(f"Deterministic guardrail extraction failed: {e}")

    advisory_block = ""
    logs = []
    if guardrails:
        advisory_block = (
            "### SYSTEM RISK ADVISORY (DETERMINISTIC) ###\n"
            + "\n".join(guardrails)
            + "\n\n"
        )
        logs.append(
            SystemMessage(content="🚨 [SYSTEM] Deterministic Risk Advisory injected.")
        )

    # 2. Build a single, high-authority instruction block.
    final_instruction = (
        f"{system_prompt}\n\n"
        f"{advisory_block}"
        "### RAW DATA FOR SYNTHESIS ###\n"
        f"{context_fallback}\n\n"
        "### CRITICAL FINAL INSTRUCTIONS ###\n"
        "1. You are the CRO. Write the FULL, UNABRIDGED Executive Credit Risk Assessment.\n"
        "2. Do NOT skip any sections. You MUST generate sections 1, 2, 3, 4, 5, and 6.\n"
        "3. Your response MUST START EXACTLY with '# Executive Credit Risk Assessment'.\n"
        "4. DO NOT add any conversational filler or introductory dots ('.').\n"
        "5. Your report MUST be at least 500 words of deep analysis."
    )

    models = get_dynamic_models()
    # Use a single HumanMessage as it often gets better adherence in Flash models
    inputs: list[BaseMessage] = [HumanMessage(content=final_instruction)]

    response, invoke_logs = invoke_with_fallback(models, inputs, "CRO")
    return {"messages": logs + invoke_logs + [response]}


def monitor_node(state: AgentState):
    """
    Agent 4: Monitoring / Quality Assurance.
    Focus: Scoring the final report using the LLM-as-a-Judge.
    """
    messages = state["messages"]
    company_id = state.get("company_id", "Unknown")

    # 1. Extract inputs and results
    input_query = ""
    for m in messages:
        if isinstance(m, HumanMessage):
            input_query = str(m.content)
            break

    final_report = str(messages[-1].content)

    # 2. Extract context data (Tool outputs)
    context_data = []
    for m in messages:
        # LangChain ToolMessages have 'content' and usually 'name' or 'tool_call_id'
        if hasattr(m, "tool_call_id") or "ToolMessage" in str(type(m)):
            name = getattr(m, "name", "Tool")
            context_data.append(f"Source: {name}\nContent: {m.content}")

    context_str = "\n\n".join(context_data)

    # 3. Run Monitoring
    try:
        verdict_data = log_live_performance(
            input_query=input_query,
            agent_response=final_report,
            context_data=context_str,
            company_id=company_id,
        )

        # Inject a system message with the scores for traceability in the UI
        score_summary = verdict_data.get("overall_summary", "No summary available.")
        score_msg = (
            f"✨ [MONITOR] Quality Scores: "
            f"Relevance={verdict_data.get('relevance', {}).get('score', '?')}/5, "
            f"Faithfulness={verdict_data.get('faithfulness', {}).get('score', '?')}/5\n"
            f"Evaluation: {score_summary}"
        )
        return {"messages": [SystemMessage(content=score_msg)]}
    except Exception as e:
        logger.warning(f"Monitoring node failed: {e}")
        return {
            "messages": [
                SystemMessage(content="⚠️ [MONITOR] Evaluation skipped due to error.")
            ]
        }


# --- Conditional Logic ---


def route_financial_analyst(state: AgentState):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and getattr(last_msg, "tool_calls", None):
        return "financial_tools"
    return "data_scientist"  # Move to next agent when done


def route_data_scientist(state: AgentState):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and getattr(last_msg, "tool_calls", None):
        return "ml_tools"
    return "orchestrator"  # Move to final report


# --- Graph Construction ---
workflow = StateGraph(AgentState)

workflow.add_node("financial_analyst", financial_analyst_node)
workflow.add_node("financial_tools", ToolNode(financial_tools_list))
workflow.add_node("data_scientist", data_scientist_node)
workflow.add_node("ml_tools", ToolNode(ml_tools_list))
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("monitor", monitor_node)

workflow.set_entry_point("financial_analyst")

workflow.add_conditional_edges(
    "financial_analyst",
    route_financial_analyst,
)
workflow.add_edge("financial_tools", "financial_analyst")  # Loop back

workflow.add_conditional_edges(
    "data_scientist",
    route_data_scientist,
)
workflow.add_edge("ml_tools", "data_scientist")  # Loop back

workflow.add_edge("orchestrator", "monitor")
workflow.add_edge("monitor", END)

app = workflow.compile()
