"""
Extended Unit tests for graph.py.

This module tests the orchestrator logic, fallbacks, and routing.
"""

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage

from src.agents.graph import (
    AgentState,
    invoke_with_fallback,
    route_data_scientist,
    route_financial_analyst,
)


def test_route_financial_analyst_to_tools():
    """Test routing when tool calls are present."""
    msg = AIMessage(
        content="", tool_calls=[{"name": "fetch_company_data", "args": {}, "id": "1"}]
    )
    state: AgentState = {"messages": [msg], "company_id": "123"}
    assert route_financial_analyst(state) == "financial_tools"


def test_route_financial_analyst_to_scientist():
    """Test routing when no tool calls are present."""
    msg = AIMessage(content="Analysis done")
    state: AgentState = {"messages": [msg], "company_id": "123"}
    assert route_financial_analyst(state) == "data_scientist"


def test_route_data_scientist_to_tools():
    """Test routing when tool calls are present."""
    msg = AIMessage(
        content="",
        tool_calls=[{"name": "get_credit_risk_score", "args": {}, "id": "2"}],
    )
    state: AgentState = {"messages": [msg], "company_id": "123"}
    assert route_data_scientist(state) == "ml_tools"


def test_route_data_scientist_to_orchestrator():
    """Test routing when no tool calls are present."""
    msg = AIMessage(content="ML prediction done")
    state: AgentState = {"messages": [msg], "company_id": "123"}
    assert route_data_scientist(state) == "orchestrator"


def test_invoke_with_fallback_primary_success():
    """Test that it uses the primary model if it succeeds."""
    mock_model = MagicMock()
    mock_model.model_name = "primary-model"
    mock_model.invoke.return_value = AIMessage(content="Success")

    models = [mock_model, None, None]
    inputs = [HumanMessage(content="Hello")]

    response, logs = invoke_with_fallback(models, inputs, "TestAgent")

    assert response.content == "Success"
    assert len(logs) == 0
    mock_model.invoke.assert_called_once()


def test_invoke_with_fallback_retry_success():
    """Test that it falls back to the second model if the first fails."""
    mock_model1 = MagicMock()
    mock_model1.model_name = "primary-model"
    mock_model1.invoke.side_effect = Exception("Fail")

    mock_model2 = MagicMock()
    mock_model2.model_name = "fallback-model"
    mock_model2.invoke.return_value = AIMessage(content="Success after fallback")

    models = [mock_model1, mock_model2, None]
    inputs = [HumanMessage(content="Hello")]

    response, logs = invoke_with_fallback(models, inputs, "TestAgent")

    assert response.content == "Success after fallback"
    assert any("Falling back to 1st Fallback" in m.content for m in logs)
    mock_model1.invoke.assert_called_once()
    mock_model2.invoke.assert_called_once()


def test_invoke_with_fallback_all_fail():
    """Test that it returns an error message if all models fail."""
    mock_model1 = MagicMock()
    mock_model1.model_name = "primary-model"
    mock_model1.invoke.side_effect = Exception("Fail 1")

    models = [mock_model1]
    inputs = [HumanMessage(content="Hello")]

    response, logs = invoke_with_fallback(models, inputs, "TestAgent")

    assert "Error: All tiers failed" in response.content
    assert any("failed" in m.content for m in logs)
