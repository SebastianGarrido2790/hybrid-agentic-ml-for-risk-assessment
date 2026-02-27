"""
Machine Learning API Tool for the Agentic Reasoning Engine.

This module defines the `get_credit_risk_score` tool, which wraps the external
FastAPI prediction service. It handles the HTTP communication, validation of inputs
using Pydantic, and graceful error handling for the agent.
"""

import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import pandas as pd
from pathlib import Path
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
            "ingresos": float(row["ingresos"]),
            "ebitda": float(row["ebitda"]),
            "activos_totales": float(row["activos_totales"]),
            "pasivos_totales": float(row["pasivos_totales"]),
            "patrimonio": float(row["patrimonio"]),
            "caja": float(row["caja"]),
            "gastos_intereses": float(row["gastos_intereses"]),
            "cuentas_cobrar": float(row["cuentas_cobrar"]),
            "inventario": float(row["inventario"]),
            "cuentas_pagar": float(row["cuentas_pagar"]),
            "sector_risk_score": float(row["sector_risk_score"]),
            "years_operating": int(row["years_operating"]),
            "ratio_mora": float(row["ratio_mora"]),
            "ratio_utilizacion": float(row["ratio_utilizacion"]),
            "revenue_growth": float(row["revenue_growth"]),
            "margen_beneficio": float(row["margen_beneficio"]),
            "score_buro": int(row["score_buro"]),
            "ebitda_margin": float(row["ebitda_margin"]),
            "debt_to_equity": float(row["debt_to_equity"]),
            "current_ratio": float(row["current_ratio"]),
        }

    except Exception as e:
        logger.error(f"Error preparing payload for company {company_id}: {e}")
        return f"Error: Failed to prepare data. {e}"

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
