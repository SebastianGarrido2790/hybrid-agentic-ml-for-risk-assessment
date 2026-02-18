"""
Feature Engineering Module for ACRAS.

This module is responsible for:
- Translating raw Spanish column names to English.
- Calculating key financial ratios (EBITDA Margin, Debt-to-Equity, Current Ratio).
- Handling data safety (inf values, missing values).
"""

import pandas as pd
import numpy as np


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw merged data into predictive features.

    Args:
        df (pd.DataFrame): Raw merged dataframe from Ingestion.

    Returns:
        pd.DataFrame: Dataframe with English column names and calculated ratios.
    """
    df = df.copy()

    # 1. Column Translation (Spanish -> English)
    mapping = {
        "riesgo_sector": "sector_risk_score",
        "anos_operando": "years_operating",
        "crecimiento_ingresos": "revenue_growth",
        "default_12m": "target",
        "pd_verdadera": "default_probability",
    }
    df = df.rename(columns=mapping)

    # 2. Financial Ratio Calculation
    # EBITDA Margin: Operating profitability (Profit / Revenue)
    # Using 'ingresos' (Revenue) and 'ebitda'
    if "ebitda" in df.columns and "ingresos" in df.columns:
        df["ebitda_margin"] = np.where(
            df["ingresos"] != 0, df["ebitda"] / df["ingresos"], 0
        )

    # Debt to Equity: Leverage (Total Liabilities / Equity)
    # Using 'pasivos_totales' and 'patrimonio'
    if "pasivos_totales" in df.columns and "patrimonio" in df.columns:
        df["debt_to_equity"] = np.where(
            df["patrimonio"] != 0,
            df["pasivos_totales"] / df["patrimonio"],
            10.0,  # High risk cap for insolvent entities
        )

    # Current Ratio: Liquidity (Current Assets / Current Liabilities)
    # Formula from report: (caja + cuentas_cobrar + inventario) / cuentas_pagar
    if all(
        col in df.columns
        for col in ["caja", "cuentas_cobrar", "inventario", "cuentas_pagar"]
    ):
        current_assets = df["caja"] + df["cuentas_cobrar"] + df["inventario"]
        df["current_ratio"] = np.where(
            df["cuentas_pagar"] != 0, current_assets / df["cuentas_pagar"], 0.0
        )

    # 3. Data Cleaning & Safety
    # Replace infinite values with 0
    df = df.replace([np.inf, -np.inf], 0)

    # Fill remaining NaNs from any transformations
    df = df.fillna(0)

    # Type Casting
    if "target" in df.columns:
        df["target"] = df["target"].astype(int)
    if "years_operating" in df.columns:
        df["years_operating"] = df["years_operating"].astype(int)

    return df
