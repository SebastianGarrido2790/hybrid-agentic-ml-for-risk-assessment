from langchain_core.messages import HumanMessage, AIMessage
from src.agents.graph import workflow, AgentState
import sys

state: AgentState = {
    "messages": [
        HumanMessage(content="Please assess credit risk for Company ID 59."),
        AIMessage(
            content="### 1. Liquidity & Solvency Breakdown\n- Current Ratio: 2.18\n### Summary\nEverything looks good."
        ),
    ],
    "company_id": "59",
}

app = workflow.compile()

# We can't invoke app directly starting at data scientist without a bit of setup. Let's run just node.
from src.agents.graph import data_scientist_node

try:
    result = data_scientist_node(state)
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print("TOOL CALLS:")
            print(msg.tool_calls)
        if hasattr(msg, "content") and msg.content:
            print("CONTENT:")
            print(msg.content.encode("utf-8", "ignore").decode("utf-8"))
except Exception as e:
    import traceback

    traceback.print_exc()
