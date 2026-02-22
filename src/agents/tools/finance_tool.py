"""
Financial Analysis Tools for the Agentic Reasoning Engine.

This module contains deterministic tool definitions for calculating standard
financial ratios. These tools are used by the agent to perform accurate mathematical
calculations instead of relying on the LLM's internal (and potentially hallucinated) math capabilities.
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class DebtToEquityInput(BaseModel):
    total_liabilities: float = Field(..., description="Total Liabilities")
    shareholders_equity: float = Field(..., description="Shareholders Equity")


class EBITDAMarginInput(BaseModel):
    ebitda: float = Field(
        ...,
        description="Earnings Before Interest, Taxes, Depreciation, and Amortization",
    )
    revenue: float = Field(..., description="Total Revenue")


class CurrentRatioInput(BaseModel):
    current_assets: float = Field(..., description="Current Assets")
    current_liabilities: float = Field(..., description="Current Liabilities")


class RevenueGrowthInput(BaseModel):
    current_revenue: float = Field(..., description="Current Period Revenue")
    previous_revenue: float = Field(..., description="Previous Period Revenue")


@tool("calculate_debt_to_equity", args_schema=DebtToEquityInput)
def calculate_debt_to_equity(
    total_liabilities: float, shareholders_equity: float
) -> str:
    """Calculates the Debt-to-Equity ratio."""
    if shareholders_equity == 0:
        return "Error: Division by zero (Shareholders Equity is 0)"
    return str(round(total_liabilities / shareholders_equity, 2))


@tool("calculate_ebitda_margin", args_schema=EBITDAMarginInput)
def calculate_ebitda_margin(ebitda: float, revenue: float) -> str:
    """Calculates the EBITDA margin."""
    if revenue == 0:
        return "Error: Division by zero (Revenue is 0)"
    return str(round(ebitda / revenue, 2))


@tool("calculate_current_ratio", args_schema=CurrentRatioInput)
def calculate_current_ratio(current_assets: float, current_liabilities: float) -> str:
    """Calculates the Current Ratio."""
    if current_liabilities == 0:
        return "Error: Division by zero (Current Liabilities is 0)"
    return str(round(current_assets / current_liabilities, 2))


@tool("calculate_revenue_growth", args_schema=RevenueGrowthInput)
def calculate_revenue_growth(current_revenue: float, previous_revenue: float) -> str:
    """Calculates the year-over-year revenue growth percentage."""
    if previous_revenue == 0:
        return "Error: Division by zero (Previous Revenue is 0)"
    growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
    return f"{growth:.2f}%"
