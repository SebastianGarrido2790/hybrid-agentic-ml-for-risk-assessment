"""
Feature Engineering Module.

This module handles column translation, financial ratio calculations, and safe handling of
missing/infinite values for the credit risk assessment system.
"""

import pandas as pd
import numpy as np


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates financial ratios and translates columns to English schema.

    Args:
        df (pd.DataFrame): Merged raw DataFrame.

    Returns:
        pd.DataFrame: DataFrame with calculated features.
    """
    # Translation & Mapping
    df = df.rename(
        columns={
            "riesgo_sector": "sector_risk_score",
            "anos_operando": "years_operating",
            "crecimiento_ventas": "revenue_growth",
            "default_12m": "target",
            "pd_verdadera": "default_probability",
        }
    )

    # Calculate Ratios
    # EBITDA Margin = EBITDA / Revenue (ingresos)
    # Using safe division handling 0 denominators
    df["ebitda_margin"] = df["ebitda"] / df["ingresos"].replace(0, np.nan)

    # Debt to Equity = Total Liab / Equity (patrimonio)
    df["debt_to_equity"] = df["pasivos_totales"] / df["patrimonio"].replace(0, np.nan)

    # Current Ratio Proxy = (Cash + AR + Inventory) / AP
    # Assuming AP ('cuentas_pagar') ~ Current Liabilities proxy
    current_assets = df["caja"] + df["cuentas_cobrar"] + df["inventario"]
    df["current_ratio"] = current_assets / df["cuentas_pagar"].replace(0, np.nan)

    # Fill NaNs from division by zero with safe defaults (e.g. 0 or median)
    # Using 0 for simplicity in ratios where denominator is 0
    df = df.fillna(
        {
            "ebitda_margin": 0,
            "debt_to_equity": 10,  # High default for inf debt/equity? Or 0? Let's use median later or 0 now.
            "current_ratio": 0,
        }
    )

    # Cap inf values if any
    df = df.replace([np.inf, -np.inf], 0)

    # Cast target to int if it became float during aggregation/merge
    if "target" in df.columns:
        df["target"] = df["target"].astype(int)

    return df
