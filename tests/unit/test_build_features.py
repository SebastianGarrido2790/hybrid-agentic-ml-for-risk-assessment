"""
Unit tests for build_features.py.

This module contains tests for feature engineering logic, including
column translations and financial ratio calculations.
"""

import pandas as pd

from src.features.build_features import engineer_features


def test_engineer_features_translations():
    """
    Tests if feature columns are correctly translated from Spanish to English.
    """
    # Setup
    df = pd.DataFrame(
        {
            "riesgo_sector": [1.5],
            "anos_operando": [5],
            "crecimiento_ventas": [0.1],
            "default_12m": [0],
            "pd_verdadera": [0.05],
        }
    )

    # Execute
    result = engineer_features(df)

    # Verify translations
    expected_cols = [
        "sector_risk_score",
        "years_operating",
        "revenue_growth",
        "target",
        "default_probability",
    ]
    for col in expected_cols:
        assert col in result.columns


def test_engineer_features_ratios():
    # Setup
    df = pd.DataFrame(
        {
            "ingresos": [1000],
            "ebitda": [200],
            "pasivos_totales": [500],
            "patrimonio": [1000],
            "caja": [100],
            "cuentas_cobrar": [200],
            "inventario": [300],
            "cuentas_pagar": [300],
        }
    )

    # Execute
    result = engineer_features(df)

    # Verify ratios
    assert result.iloc[0]["ebitda_margin"] == 0.2
    assert result.iloc[0]["debt_to_equity"] == 0.5
    assert result.iloc[0]["current_ratio"] == 2.0


def test_engineer_features_division_by_zero():
    # Setup
    df = pd.DataFrame(
        {
            "ingresos": [0],
            "ebitda": [200],
            "pasivos_totales": [500],
            "patrimonio": [0],
            "caja": [100],
            "cuentas_cobrar": [200],
            "inventario": [300],
            "cuentas_pagar": [0],
        }
    )

    # Execute
    result = engineer_features(df)

    # Verify fallback for zero divisions
    assert result.iloc[0]["ebitda_margin"] == 0.0
    assert result.iloc[0]["debt_to_equity"] == 10.0
    assert result.iloc[0]["current_ratio"] == 0.0
