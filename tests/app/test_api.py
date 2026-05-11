"""
API Endpoint Tests.

Verifies the functionality of the Prediction Service endpoints:
- /health: Service status check.
- /predict: Risk prediction logic (Low/High risk scenarios).
- /metrics: Prometheus metrics exposure.
"""

from fastapi import status


def test_health_check(client):
    response = client.get("/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ACRAS-API"
    assert "model_version" in data


def test_predict_success(client, mock_model):
    # Valid input payload
    payload = {
        "ingresos": 5000000,
        "ebitda": 1000000,
        "activos_totales": 2000000,
        "pasivos_totales": 800000,
        "patrimonio": 1200000,
        "caja": 200000,
        "gastos_intereses": 50000,
        "cuentas_cobrar": 150000,
        "inventario": 100000,
        "cuentas_pagar": 80000,
        "sector_risk_score": 3.5,
        "years_operating": 5,
        "ratio_mora": 0.02,
        "ratio_utilizacion": 0.4,
        "revenue_growth": 0.1,
        "margen_beneficio": 0.2,
        "score_buro": 750,
        "ebitda_margin": 0.2,
        "debt_to_equity": 0.66,
        "current_ratio": 2.0,
    }

    mock_model.predict.return_value = [0]
    mock_model.predict_proba.return_value = [[0.8, 0.2]]  # 0.2 < 0.3 -> Low Risk

    response = client.post("/v1/predict", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["prediction"] == 0
    assert data["probability"] == 0.2
    assert data["risk_level"] == "Low"


def test_predict_high_risk(client, mock_model):
    # Valid input payload
    payload = {
        "ingresos": 5000000,
        "ebitda": 1000000,
        "activos_totales": 2000000,
        "pasivos_totales": 800000,
        "patrimonio": 1200000,
        "caja": 200000,
        "gastos_intereses": 50000,
        "cuentas_cobrar": 150000,
        "inventario": 100000,
        "cuentas_pagar": 80000,
        "sector_risk_score": 3.5,
        "years_operating": 5,
        "ratio_mora": 0.02,
        "ratio_utilizacion": 0.4,
        "revenue_growth": 0.1,
        "margen_beneficio": 0.2,
        "score_buro": 750,
        "ebitda_margin": 0.2,
        "debt_to_equity": 0.66,
        "current_ratio": 2.0,
    }

    mock_model.predict.return_value = [1]
    mock_model.predict_proba.return_value = [[0.1, 0.9]]  # 0.9 > 0.7 -> High Risk

    response = client.post("/v1/predict", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["prediction"] == 1
    assert data["probability"] == 0.9
    assert data["risk_level"] == "High"


def test_predict_medium_risk(client, mock_model):
    # Valid input payload
    payload = {
        "ingresos": 5000000,
        "ebitda": 1000000,
        "activos_totales": 2000000,
        "pasivos_totales": 800000,
        "patrimonio": 1200000,
        "caja": 200000,
        "gastos_intereses": 50000,
        "cuentas_cobrar": 150000,
        "inventario": 100000,
        "cuentas_pagar": 80000,
        "sector_risk_score": 3.5,
        "years_operating": 5,
        "ratio_mora": 0.02,
        "ratio_utilizacion": 0.4,
        "revenue_growth": 0.1,
        "margen_beneficio": 0.2,
        "score_buro": 750,
        "ebitda_margin": 0.2,
        "debt_to_equity": 0.66,
        "current_ratio": 2.0,
    }

    mock_model.predict.return_value = [0]
    mock_model.predict_proba.return_value = [[0.5, 0.5]]  # 0.5 -> Medium Risk

    response = client.post("/v1/predict", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["prediction"] == 0
    assert data["probability"] == 0.5
    assert data["risk_level"] == "Medium"


def test_predict_validation_error(client):
    # Invalid payload (missing required field 'ingresos')
    payload = {"ebitda": 1000000}
    response = client.post("/v1/predict", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_health_service_not_ready(client):
    # Temporarily remove model to simulate uninitialized state during app start
    if hasattr(client.app.state, "model"):
        del client.app.state.model
    response = client.get("/v1/health")
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


# Optional: Metrics check
def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == status.HTTP_200_OK


def test_predict_extra_fields(client):
    """Test that extra fields are forbidden by the Pydantic schema."""
    payload = {"annual_revenue": 5000000, "extra_field": "should_fail"}
    response = client.post("/v1/predict", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # We can check the error message to ensure it's a 'forbid' error if needed
    assert "extra_field" in response.text


def test_global_exception_handler(client, mock_model):
    """Test that unhandled exceptions are caught by the global handler."""
    mock_model.predict.side_effect = Exception("Internal Crash")

    payload = {
        "ingresos": 5000000,
        "ebitda": 1000000,
        "activos_totales": 2000000,
        "pasivos_totales": 800000,
        "patrimonio": 1200000,
        "caja": 200000,
        "gastos_intereses": 50000,
        "cuentas_cobrar": 150000,
        "inventario": 100000,
        "cuentas_pagar": 80000,
        "sector_risk_score": 3.5,
        "years_operating": 5,
        "ratio_mora": 0.02,
        "ratio_utilizacion": 0.4,
        "revenue_growth": 0.1,
        "margen_beneficio": 0.2,
        "score_buro": 750,
        "ebitda_margin": 0.2,
        "debt_to_equity": 0.66,
        "current_ratio": 2.0,
    }

    response = client.post("/v1/predict", json=payload)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "internal processing error" in response.json()["detail"].lower()
