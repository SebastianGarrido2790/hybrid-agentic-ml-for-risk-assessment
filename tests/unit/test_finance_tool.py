"""
Unit tests for finance_tool.py.

This module tests the financial calculation tools used by the AI Agent.
"""

from src.agents.tools.finance_tool import (
    calculate_current_ratio,
    calculate_debt_to_equity,
    calculate_ebitda_margin,
    calculate_revenue_growth,
)


def test_calculate_debt_to_equity():
    """
    Tests the debt-to-equity ratio calculation tool.
    """
    assert (
        calculate_debt_to_equity.invoke(
            {"total_liabilities": 500.0, "shareholders_equity": 1000.0}
        )
        == "0.5"
    )
    assert (
        calculate_debt_to_equity.invoke(
            {"total_liabilities": 500.0, "shareholders_equity": 0}
        )
        == "Error: Division by zero (Shareholders Equity is 0)"
    )


def test_calculate_ebitda_margin():
    assert calculate_ebitda_margin.invoke({"ebitda": 200.0, "revenue": 1000.0}) == "0.2"
    assert (
        calculate_ebitda_margin.invoke({"ebitda": 200.0, "revenue": 0})
        == "Error: Division by zero (Revenue is 0)"
    )


def test_calculate_current_ratio():
    assert (
        calculate_current_ratio.invoke(
            {"current_assets": 600.0, "current_liabilities": 300.0}
        )
        == "2.0"
    )
    assert (
        calculate_current_ratio.invoke(
            {"current_assets": 600.0, "current_liabilities": 0}
        )
        == "Error: Division by zero (Current Liabilities is 0)"
    )


def test_calculate_revenue_growth():
    assert (
        calculate_revenue_growth.invoke(
            {"current_revenue": 1100.0, "previous_revenue": 1000.0}
        )
        == "10.00%"
    )
    assert (
        calculate_revenue_growth.invoke(
            {"current_revenue": 1100.0, "previous_revenue": 0}
        )
        == "Error: Division by zero (Previous Revenue is 0)"
    )
