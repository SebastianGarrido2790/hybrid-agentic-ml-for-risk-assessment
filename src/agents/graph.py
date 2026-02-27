"""
Multi-Agent Orchestrator for ACRAS.

This module implements a "Relay Team" pattern where specialized agents pass
the task context to each other:
1. Financial Analyst: Fetches data and calculates ratios.
2. Data Scientist: Predicts default probability using the ML API.
3. Orchestrator (CRO): Synthesizes the final report.

The architecture incorporates hot-swapping logic via dynamic imports and
configuration factories, allowing for runtime model updates and tool
re-binding without system downtime.
"""

from typing import Annotated, TypedDict, List, Optional, Tuple
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from src.agents.tools.ml_api_tool import get_credit_risk_score
from src.agents.tools.lookup_tool import fetch_company_data
from src.agents.tools.finance_tool import (
    calculate_debt_to_equity,
    calculate_ebitda_margin,
    calculate_current_ratio,
    calculate_revenue_growth,
)
import importlib
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
    calculate_revenue_growth,
]
ml_tools_list = [
    get_credit_risk_score,
]


def get_dynamic_models(tools_list: Optional[List] = None):
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
    except Exception:
        m_primary = None

    # 2. Fallback 1 (Dynamic switch)
    try:
        if current_settings.DEFAULT_LLM_PROVIDER == "huggingface":
            m_fb1 = factory_module.get_llm(
                provider="gemini", model_name=current_settings.GEMINI_POWER_MODEL
            )
        else:
            m_fb1 = factory_module.get_llm(provider="huggingface")
    except Exception:
        m_fb1 = None

    # 3. Fallback 2 (Lite)
    try:
        m_fb2 = factory_module.get_llm(
            provider="gemini", model_name=current_settings.GEMINI_LITE_MODEL
        )
    except Exception:
        m_fb2 = None

    raw_models = [m_primary, m_fb1, m_fb2]

    if tools_list:
        return bind_tools_to_all(tools_list, fallback_models=raw_models)
    return raw_models


def bind_tools_to_all(tools, fallback_models: List):
    """Refactored helper for dynamic binding"""
    bound = []
    for m in fallback_models:
        if m:
            try:
                bound.append(m.bind_tools(tools))
            except Exception:
                bound.append(m)
        else:
            bound.append(None)
    return bound


# --- Helper for Fallback ---
def invoke_with_fallback(
    models_tier: List, inputs, agent_name="Agent"
) -> Tuple[BaseMessage, List[BaseMessage]]:
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
            # OPTIMIZATION: If not using a native Tier 1 LLM (like Gemini),
            # or if it's the 1st/2nd fallback, merge instructions into the prompt.
            if (
                i > 0
                or "qwen" in model_info
                or "meta" in model_info
                or "mistral" in model_info
            ):
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
                        "### CURRENT DATA & CONTEXT ###\n"
                        f"{last_msg.content or ''}\n\n"
                        "ASSISTANCE_READY: True\n"
                        "RESPONSE STRUCTURE: Follow mandatory sections strictly."
                    )
                    new_last_msg = HumanMessage(content=new_content)
                    final_inputs = user_messages[:-1] + [new_last_msg]
                else:
                    final_inputs = [HumanMessage(content=system_instruction)]
            else:
                final_inputs = inputs

            print(f"🤖 {agent_name} -> Calling {tier_name} ({model_info})...")
            if i > 0:
                logs.append(
                    SystemMessage(
                        content=f"🔄 Falling back to {tier_name} ({model_info})..."
                    )
                )

            return model.invoke(final_inputs), logs

        except Exception as e:
            error_msg = f"Tier {i + 1} ({tier_name} - {model_info}) failed: {str(e)}"
            print(f"⚠️ {agent_name}: {error_msg}")
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

    models = get_dynamic_models(ml_tools_list)
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

    importlib.reload(prompts_module)  # Requires a "module object" to work
    system_prompt = getattr(prompts_module, "ORCHESTRATOR_SYSTEM_PROMPT")

    models = get_dynamic_models()
    inputs = [SystemMessage(content=system_prompt)] + messages
    response, logs = invoke_with_fallback(models, inputs, "CRO")
    return {"messages": logs + [response]}


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
