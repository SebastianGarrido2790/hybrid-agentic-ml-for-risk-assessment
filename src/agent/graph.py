"""
LangGraph Orchestrator for the Agentic Reasoning Engine.

This module defines the state graph that orchestrates the agent's workflow.
It connects the Agent node (LLM) with the Tools node and defines the conditional
logic for routing messages and managing the conversation state.
"""

from typing import Annotated, TypedDict, Union, Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage
from src.agent.tools.ml_api_tool import get_credit_risk_score
from src.agent.tools.finance_tool import (
    calculate_debt_to_equity,
    calculate_ebitda_margin,
    calculate_current_ratio,
)
from src.agent.model_factory import get_llm
import operator


# Define the State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]


# Initialize Tools
tools = [
    get_credit_risk_score,
    calculate_debt_to_equity,
    calculate_ebitda_margin,
    calculate_current_ratio,
]

# Initialize LLM with Tools
llm = get_llm(provider="gemini")  # Default to Gemini
llm_with_tools = llm.bind_tools(tools)


# Define Nodes
def call_model(state: AgentState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> Union[Literal["tools"], Literal[END]]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END


# Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
)

workflow.add_edge("tools", "agent")

# Compile
app = workflow.compile()
