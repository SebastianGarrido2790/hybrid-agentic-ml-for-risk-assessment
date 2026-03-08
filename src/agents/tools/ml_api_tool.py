"""
Machine Learning API Tool for the Agentic Reasoning Engine.

This module defines the `get_credit_risk_score` tool, which wraps the external
FastAPI prediction service. It handles the HTTP communication, validation of inputs
using Pydantic, and graceful error handling for the agent.
"""

from pathlib import Path

import pandas as pd
import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.agents.config import get_agent_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_agent_settings()


class PredictionInput(BaseModel):
    """Schema for the ML API Input to the tool."""

    company_id: int = Field(..., description="ID of the company to evaluate")


@tool("get_credit_risk_score", args_schema=PredictionInput)
def get_credit_risk_score(company_id: int) -> str:
    """
    Queries the Machine Learning API to get a quantitative credit risk assessment.
    Returns a string containing the Risk Level (Low/Medium/High) and the Probability of Default.
    """
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    DATA_PATH = BASE_DIR / "artifacts" / "data_ingestion" / "val.csv"

    try:
        if not DATA_PATH.exists():
            return f"Error: Database file not found at {DATA_PATH}"

        df = pd.read_csv(DATA_PATH)
        record = df[df["id_empresa"] == company_id]

        if record.empty:
            return f"Error: Company ID {company_id} not found."

        row = record.iloc[0]

        payload = {
            "annual_revenue": float(row["ingresos"]),
            "ebitda": float(row["ebitda"]),
            "total_assets": float(row["activos_totales"]),
            "total_liabilities": float(row["pasivos_totales"]),
            "total_equity": float(row["patrimonio"]),
            "cash": float(row["caja"]),
            "interest_expenses": float(row["gastos_intereses"]),
            "accounts_receivable": float(row["cuentas_cobrar"]),
            "inventory": float(row["inventario"]),
            "accounts_payable": float(row["cuentas_pagar"]),
            "sector_risk_score": float(row["sector_risk_score"]),
            "years_operating": int(row["years_operating"]),
            "delinquency_ratio": float(row["ratio_mora"]),
            "credit_utilization": float(row["ratio_utilizacion"]),
            "revenue_growth": float(row["revenue_growth"]),
            "profit_margin": float(row["margen_beneficio"]),
            "bureau_score": int(row["score_buro"]),
            "ebitda_margin": float(row["ebitda_margin"]),
            "debt_to_equity": float(row["debt_to_equity"]),
            "current_ratio": float(row["current_ratio"]),
        }

    except Exception as e:
        logger.error(f"Error preparing payload for company {company_id}: {e}")
        return f"Error: Failed to prepare data. {e}"

    try:
        # Increase timeout to 10 or 15 seconds if you experience "Agentic Timeout" errors in larger batches
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
