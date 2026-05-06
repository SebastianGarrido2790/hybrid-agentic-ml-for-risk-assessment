"""
Lookup Tools for the Agentic Reasoning Engine.

This module provides tools for fetching raw company data from internal
CSV databases (e.g., validation datasets) for agents to analyze.

`@lru_cache(maxsize=1)` decorator ensures the validation dataset (CSV) is loaded into
memory only once and reused across all subsequent tool calls within the same process.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd
from langchain_core.tools import tool

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Define path to the "Database" (Validation CSV)
# Assumes the script runs from project root or src is in path.
# We will resolve it relative to this file's location.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_PATH = BASE_DIR / "artifacts" / "data_ingestion" / "val.csv"


@lru_cache(maxsize=1)
def _get_database() -> pd.DataFrame:
    """Internal helper to load and cache the validation database."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Database file not found at {DATA_PATH}")
    return pd.read_csv(DATA_PATH)


@tool("fetch_company_data")
def fetch_company_data(company_id: int) -> str:
    """
    Fetches financial data for a company by its ID (id_empresa) from the internal database.
    Returns a dictionary of financial metrics or an error message if not found.
    Useful for the Financial Analyst to get raw data before calculating ratios.
    """
    try:
        # Load data with caching
        df = _get_database()

        # Ensure ID is int
        record = df[df["id_empresa"] == company_id]

        if record.empty:
            return f"Error: Company ID {company_id} not found."

        # Convert to dict
        data = record.iloc[0].to_dict()

        # Clean up numpy types to native python types for JSON serialization
        clean_data = {}
        for k, v in data.items():
            if k in ["target", "default_probability"]:
                continue
            if pd.isna(v):
                clean_data[k] = None
            else:
                clean_data[k] = v

        return str(clean_data)

    except Exception as e:
        logger.error(f"Error fetching company data: {e}")
        return f"Error: Failed to fetch data. {e}"
