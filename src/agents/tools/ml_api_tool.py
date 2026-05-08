"""
Machine Learning API Tool for the Agentic Reasoning Engine.

This module defines the `get_credit_risk_score` tool, which wraps the external
FastAPI prediction service. It handles the HTTP communication, validation of inputs
using Pydantic, and graceful error handling for the agent.

OpenTelemetry tracing is integrated to monitor tool execution.

`@lru_cache(maxsize=1)` decorator ensures the validation dataset (CSV) is loaded into
memory only once and reused across all subsequent tool calls within the same process.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd
import requests
from langchain_core.tools import tool
from opentelemetry import trace
from pydantic import BaseModel, Field

from src.agents.config import get_agent_settings
from src.utils.logger import get_logger

tracer = trace.get_tracer("acras")

logger = get_logger(__name__)
settings = get_agent_settings()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_PATH = BASE_DIR / "artifacts" / "data_ingestion" / "val.csv"


@lru_cache(maxsize=1)
def _get_database() -> pd.DataFrame:
    """Internal helper to load and cache the validation database."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Database file not found at {DATA_PATH}")
    return pd.read_csv(DATA_PATH)


class PredictionInput(BaseModel):
    """Schema for the ML API Input to the tool."""

    company_id: int = Field(..., description="ID of the company to evaluate")


@tool("get_credit_risk_score", args_schema=PredictionInput)
def get_credit_risk_score(company_id: int) -> str:
    """
    Queries the Machine Learning API to get a quantitative credit risk assessment.
    Returns a string containing the Risk Level (Low/Medium/High) and the Probability of Default.
    """
    with tracer.start_as_current_span("tool_execution") as span:
        span.set_attribute("gen_ai.tool.name", "get_credit_risk_score")
        try:
            # Load data with caching
            df = _get_database()
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
        except requests.exceptions.HTTPError as err:
            return f"Error: The ML Model API returned an error: {err}"
        except Exception as err:
            return (
                f"Error: An unexpected error occurred while querying the model: {err}"
            )
