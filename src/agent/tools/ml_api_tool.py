"""
Machine Learning API Tool for the Agentic Reasoning Engine.

This module defines the `get_credit_risk_score` tool, which wraps the external
FastAPI prediction service. It handles the HTTP communication, validation of inputs
using Pydantic, and graceful error handling for the agent.
"""

import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.agent.config import get_agent_settings
import logging

logger = logging.getLogger(__name__)
settings = get_agent_settings()


class PredictionInput(BaseModel):
    """Schema for the ML API Input - Must match the FastAPI schema exactly."""

    ingresos: float = Field(..., description="Annual income of the company")
    ebitda: float = Field(
        ...,
        description="Earnings Before Interest, Taxes, Depreciation, and Amortization",
    )
    activos_totales: float = Field(..., description="Total Assets")
    pasivos_totales: float = Field(..., description="Total Liabilities")
    patrimonio: float = Field(..., description="Total Equity")
    caja: float = Field(..., description="Cash on hand")
    gastos_intereses: float = Field(..., description="Interest Expenses")
    cuentas_cobrar: float = Field(..., description="Accounts Receivable")
    inventario: float = Field(..., description="Inventory value")
    cuentas_pagar: float = Field(..., description="Accounts Payable")
    sector_risk_score: float = Field(..., description="Sector risk score (0-10)")
    years_operating: int = Field(..., description="Years in operation")
    ratio_mora: float = Field(..., description="Delinquency ratio (0.0 - 1.0)")
    ratio_utilizacion: float = Field(
        ..., description="Credit utilization ratio (0.0 - 1.0)"
    )
    revenue_growth: float = Field(
        ..., description="Revenue growth rate (e.g., 0.1 for 10%)"
    )
    margen_beneficio: float = Field(..., description="Profit margin")
    score_buro: int = Field(..., description="Credit Bureau Score (300-850)")
    ebitda_margin: float = Field(..., description="EBITDA Margin")
    debt_to_equity: float = Field(..., description="Debt to Equity Ratio")
    current_ratio: float = Field(..., description="Current Ratio")


@tool("get_credit_risk_score", args_schema=PredictionInput)
def get_credit_risk_score(
    ingresos: float,
    ebitda: float,
    activos_totales: float,
    pasivos_totales: float,
    patrimonio: float,
    caja: float,
    gastos_intereses: float,
    cuentas_cobrar: float,
    inventario: float,
    cuentas_pagar: float,
    sector_risk_score: float,
    years_operating: int,
    ratio_mora: float,
    ratio_utilizacion: float,
    revenue_growth: float,
    margen_beneficio: float,
    score_buro: int,
    ebitda_margin: float,
    debt_to_equity: float,
    current_ratio: float,
) -> str:
    """
    Queries the Machine Learning API to get a quantitative credit risk assessment.
    Returns a string containing the Risk Level (Low/Medium/High) and the Probability of Default.
    Use this tool ONLY when you have all the required financial fields.
    """
    payload = {
        "ingresos": ingresos,
        "ebitda": ebitda,
        "activos_totales": activos_totales,
        "pasivos_totales": pasivos_totales,
        "patrimonio": patrimonio,
        "caja": caja,
        "gastos_intereses": gastos_intereses,
        "cuentas_cobrar": cuentas_cobrar,
        "inventario": inventario,
        "cuentas_pagar": cuentas_pagar,
        "sector_risk_score": sector_risk_score,
        "years_operating": years_operating,
        "ratio_mora": ratio_mora,
        "ratio_utilizacion": ratio_utilizacion,
        "revenue_growth": revenue_growth,
        "margen_beneficio": margen_beneficio,
        "score_buro": score_buro,
        "ebitda_margin": ebitda_margin,
        "debt_to_equity": debt_to_equity,
        "current_ratio": current_ratio,
    }

    try:
        response = requests.post(settings.ML_API_URL, json=payload, timeout=5)
        response.raise_for_status()
        data = response.json()

        return f"Risk Level: {data.get('risk_level')}, Probability of Default: {data.get('probability')}"

    except requests.exceptions.ConnectionError:
        return "Error: The ML Model API is currently unreachable. Proceed with qualitative analysis only."
    except requests.exceptions.HTTPError as e:
        return f"Error: The ML Model API returned an error: {e}"
    except Exception as e:
        return f"Error: An unexpected error occurred while querying the model: {e}"
