"""
Unit Tests for the Agentic Reasoning Engine Tools.

This module contains tests for the bespoke LangChain tools used by the agent.
It validates the functionality of the `ml_api_tool` (mocking the API response)
and ensures that tools handle valid inputs and error conditions correctly.
"""

import pytest
import requests
from unittest.mock import patch
from src.agents.tools.ml_api_tool import get_credit_risk_score


@pytest.fixture
def mock_api_response():
    return {"prediction": 0, "probability": 0.15, "risk_level": "Low"}


def test_ml_api_tool_success(mock_api_response):
    """Test successful API call."""
    with patch("src.agents.tools.ml_api_tool.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_api_response

        result = get_credit_risk_score.invoke(
            {
                "ingresos": 1000,
                "ebitda": 200,
                "activos_totales": 500,
                "pasivos_totales": 100,
                "patrimonio": 400,
                "caja": 50,
                "gastos_intereses": 10,
                "cuentas_cobrar": 20,
                "inventario": 30,
                "cuentas_pagar": 10,
                "sector_risk_score": 2.0,
                "years_operating": 5,
                "ratio_mora": 0.0,
                "ratio_utilizacion": 0.3,
                "revenue_growth": 0.1,
                "margen_beneficio": 0.2,
                "score_buro": 700,
                "ebitda_margin": 0.2,
                "debt_to_equity": 0.25,
                "current_ratio": 5.0,
            }
        )

        assert "Risk Level: Low" in result
        assert "Probability of Default: 0.15" in result


def test_ml_api_tool_failure():
    """Test API connection failure."""
    with patch("src.agents.tools.ml_api_tool.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError

        result = get_credit_risk_score.invoke(
            {
                "ingresos": 1000,
                "ebitda": 200,
                "activos_totales": 500,
                "pasivos_totales": 100,
                "patrimonio": 400,
                "caja": 50,
                "gastos_intereses": 10,
                "cuentas_cobrar": 20,
                "inventario": 30,
                "cuentas_pagar": 10,
                "sector_risk_score": 2.0,
                "years_operating": 5,
                "ratio_mora": 0.0,
                "ratio_utilizacion": 0.3,
                "revenue_growth": 0.1,
                "margen_beneficio": 0.2,
                "score_buro": 700,
                "ebitda_margin": 0.2,
                "debt_to_equity": 0.25,
                "current_ratio": 5.0,
            }
        )

        assert "Error: The ML Model API is currently unreachable" in result
