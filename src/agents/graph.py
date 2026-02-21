"""
Multi-Agent Orchestrator for ACRAS.

This module implements a "Relay Team" pattern where specialized agents pass
the task context to each other:
1. Financial Analyst: Fetches data and calculates ratios.
2. Data Scientist: Predicts default probability using the ML API.
3. Orchestrator (CRO): Synthesizes the final report.
"""

from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from src.agents.tools.ml_api_tool import get_credit_risk_score
from src.agents.tools.lookup_tool import fetch_company_data
from src.agents.tools.finance_tool import (
    calculate_debt_to_equity,
    calculate_ebitda_margin,
    calculate_current_ratio,
)
from src.agents.model_factory import get_llm
from src.agents.config import get_agent_settings
import operator


# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    company_id: str  # Context passed along


# --- Tool Sets ---
financial_tools_list = [
    fetch_company_data,
    calculate_debt_to_equity,
    calculate_ebitda_margin,
    calculate_current_ratio,
]
ml_tools_list = [
    get_credit_risk_score,
]

settings = get_agent_settings()

# --- Models ---
# TIER 1: PRIMARY - Uses Factory Default
try:
    llm_primary = get_llm()
except Exception:
    llm_primary = None

# TIER 2: FIRST FALLBACK - Dynamic (Opposite of Primary)
# If default is HF, 1st fallback is Gemini. If default is Gemini, 1st fallback is HF.
try:
    if settings.DEFAULT_LLM_PROVIDER == "huggingface":
        # Primary is HF -> 1st Fallback is Gemini Power
        llm_fallback_1 = get_llm(
            provider="gemini", model_name=settings.GEMINI_POWER_MODEL
        )
    else:
        # Primary is Gemini -> 1st Fallback is HF
        llm_fallback_1 = get_llm(provider="huggingface")
except Exception:
    llm_fallback_1 = None

# TIER 3: SECOND FALLBACK - Google Gemini Flash Lite (Ultra-Low Latency / Reliable)
try:
    llm_fallback_2 = get_llm(provider="gemini", model_name=settings.GEMINI_LITE_MODEL)
except Exception:
    llm_fallback_2 = None


# --- Startup Summary ---
print("\n" + "=" * 60)
print("🚀 ACRAS AGENT CLUSTER: ACTIVE HIERARCHY")
print("=" * 60)
print(f"PRIMARY PROVIDER: {settings.DEFAULT_LLM_PROVIDER.upper()}")
print(
    f"  └─ Tier 1 (Primary):  {settings.HF_MODEL if settings.DEFAULT_LLM_PROVIDER == 'huggingface' else settings.GEMINI_POWER_MODEL}"
)
print(
    f"  └─ Tier 2 (Fallback): {settings.GEMINI_POWER_MODEL if settings.DEFAULT_LLM_PROVIDER == 'huggingface' else settings.HF_MODEL}"
)
print(f"  └─ Tier 3 (Reliable): {settings.GEMINI_LITE_MODEL}")
print("=" * 60 + "\n")


# HELPER: Bind tools to a list of models
def bind_tools_to_all(tools):
    """
    Automatically prepares all tiers with the necessary financial and risk tools,
    ensuring that the fallback models know exactly how to fetch data even if they
    are swapped mid-run.
    """
    bound = []
    for m in [llm_primary, llm_fallback_1, llm_fallback_2]:
        if m:
            try:
                bound.append(m.bind_tools(tools))
            except Exception:
                # Some models (like simple HF ones) might not support native bind_tools
                bound.append(m)
        else:
            bound.append(None)
    return bound


fin_models = bind_tools_to_all(financial_tools_list)
ds_models = bind_tools_to_all(ml_tools_list)
cro_models = [llm_primary, llm_fallback_1, llm_fallback_2]


# --- Helper for Fallback ---
def invoke_with_fallback(models_tier: List, inputs, agent_name="Agent"):
    """
    Sequentially attempts to invoke models in the provided list (Tiers).
    Applies System Instruction optimization for the 7B models (Tier 2/HF).
    """

    for i, model in enumerate(models_tier):
        if not model:
            continue

        try:
            # OPTIMIZATION: If not the primary model (often 7B/OpenSource), merge System Prompt
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
                    new_content = (
                        f"### SYSTEM INSTRUCTION ###\n{system_instruction}\n"
                        f"### USER INPUT ###\n{last_msg.content or ''}"
                    )
                    new_last_msg = HumanMessage(content=new_content)
                    final_inputs = user_messages[:-1] + [new_last_msg]
                else:
                    final_inputs = [HumanMessage(content=system_instruction)]
            else:
                final_inputs = inputs

            tier_name = ["Primary", "1st Fallback", "2nd Fallback"][i]
            model_info = getattr(model, "model", getattr(model, "repo_id", "Unknown"))
            print(f"🤖 {agent_name} -> Calling {tier_name} ({model_info})...")

            return model.invoke(final_inputs)

        except Exception as e:
            tier_name = ["Primary", "1st Fallback", "2nd Fallback"][i]
            print(f"⚠️ {agent_name}: {tier_name} failed ({e}).")
            if i == len(models_tier) - 1:
                return SystemMessage(content=f"Error: All tiers failed. {e}")

    return SystemMessage(content="System Error: No models available.")


# --- Nodes ---


def financial_analyst_node(state: AgentState):
    """
    Agent 1: Senior Financial Analyst.
    Focus: Data extraction and metric calculation.
    """
    messages = state["messages"]
    system_prompt = (
        "You are a Senior Financial Analyst at ACRAS. "
        "Your role is to perform a deterministic financial deep-dive. "
        "INSTRUCTIONS:\n"
        "1. Use `fetch_company_data` to retrieve the core profile.\n"
        "2. Use calculation tools for: Debt-to-Equity, EBITDA Margin, and Current Ratio.\n"
        "3. Provide your output in this structure:\n"
        "### Financial Metrics Summary\n"
        "- **Liquidity:** [Metric Value] ([Brief Interpretation])\n"
        "- **Solvency:** [Metric Value] ([Brief Interpretation])\n"
        "- **Profitability:** [Metric Value] ([Brief Interpretation])\n"
        "4. Summarize the biggest financial strength and weakness detected."
    )

    inputs = [SystemMessage(content=system_prompt)] + messages
    response = invoke_with_fallback(fin_models, inputs, "Financial Analyst")
    return {"messages": [response]}


def data_scientist_node(state: AgentState):
    """
    Agent 2: Lead Data Scientist.
    Focus: ML Inference and quantitative interpretation.
    """
    messages = state["messages"]
    system_prompt = (
        "You are a Lead Data Scientist specializing in Credit Risk. "
        "Your role is to quantify default probability using the ML engine. "
        "INSTRUCTIONS:\n"
        "1. Extract the raw numeric values from the Financial Analyst's report.\n"
        "2. Call `get_credit_risk_score` with exactly: ingresos, ebitda, pasivo_circulante, activo_circulante, pasivos_totales, capital.\n"
        "3. Your output MUST include:\n"
        "### Quantitative Risk Analysis\n"
        "- **Model PD:** [Value returned by tool]\n"
        "- **Risk Tier:** [Low/Moderate/High based on PD]\n"
        "- **Model Insight:** [Brief note on which financial factor likely drove this score]"
    )
    inputs = [SystemMessage(content=system_prompt)] + messages
    response = invoke_with_fallback(ds_models, inputs, "Data Scientist")
    return {"messages": [response]}


def orchestrator_node(state: AgentState):
    """
    Agent 3: Chief Risk Officer (CRO).
    Focus: Executive synthesis and final recommendation.
    """
    messages = state["messages"]
    system_prompt = (
        "You are the Chief Risk Officer (CRO). Your task is to synthesize the final Executive Report. "
        "You MUST follow this Markdown structure strictly for the report to render correctly in PDF:\n\n"
        "# Executive Credit Risk Assessment\n"
        "## 1. Executive Summary\n"
        "[Provide a high-level overview of the credit decision and the entity's profile.]\n\n"
        "## 2. Financial Performance Analysis\n"
        "| Metric | Value | Assessment |\n"
        "| :--- | :--- | :--- |\n"
        "| Current Ratio | [Value] | [Comment] |\n"
        "| Debt-to-Equity | [Value] | [Comment] |\n"
        "| EBITDA Margin | [Value] | [Comment] |\n\n"
        "## 3. Quantitative Risk Prediction\n"
        "**Probability of Default (PD):** [Value]%\n"
        "**Scoreboard Analysis:** [Explain how the metrics translated into the risk score.]\n\n"
        "## 4. Final Directive & Conclusion\n"
        "**Recommendation:** [APPROVE / REJECT / REVIEW]\n"
        "**Rationale:** [Summarize the fatal or key deciding factor.]\n\n"
        "**Risk Score: [XX]**\n"
        "(The Risk Score must be between 0 and 100 on a single line for extraction.)"
    )
    inputs = [SystemMessage(content=system_prompt)] + messages
    response = invoke_with_fallback(cro_models, inputs, "CRO")
    return {"messages": [response]}


# --- Conditional Logic ---


def route_financial_analyst(state: AgentState):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "financial_tools"
    return "data_scientist"  # Move to next agent when done


def route_data_scientist(state: AgentState):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "ml_tools"
    return "orchestrator"  # Move to final report


# --- Graph Construction ---
workflow = StateGraph(AgentState)

workflow.add_node("financial_analyst", financial_analyst_node)
workflow.add_node("financial_tools", ToolNode(financial_tools_list))
workflow.add_node("data_scientist", data_scientist_node)
workflow.add_node("ml_tools", ToolNode(ml_tools_list))
workflow.add_node("orchestrator", orchestrator_node)

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

workflow.add_edge("orchestrator", END)

app = workflow.compile()
