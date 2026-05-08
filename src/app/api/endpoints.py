"""
API Endpoints for ACRAS.

Centralizes endpoint business logic for modular expansion.
Includes rate-limiting configurations for request throttling.
"""

import pandas as pd
from fastapi import APIRouter, HTTPException, Request, status

from src.app.schemas import PredictionInput, PredictionOutput
from src.app.core.security import limiter
from src.config.configuration import ConfigurationManager
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def health_check(request: Request):
    """
    Health check endpoint to verify service status.
    """
    # Access state from request.app.state
    if not hasattr(request.app.state, "model") or not hasattr(
        request.app.state, "preprocessor"
    ):
        raise HTTPException(
            status_code=503, detail="Service not ready (artifacts not loaded)"
        )

    model_version = getattr(request.app.state, "model_version", "unknown")
    return {"status": "ok", "service": "ACRAS-API", "model_version": model_version}


@router.post(
    "/predict", response_model=PredictionOutput, status_code=status.HTTP_200_OK
)
@limiter.limit("50/minute")
async def predict(input_data: PredictionInput, request: Request):
    """
    Predict credit risk for a given company profile.
    """
    if not hasattr(request.app.state, "model") or not hasattr(
        request.app.state, "preprocessor"
    ):
        raise HTTPException(status_code=503, detail="Model service not initialized")

    model = request.app.state.model
    preprocessor = request.app.state.preprocessor

    try:
        # Convert input Pydantic model to DataFrame
        input_df = pd.DataFrame([input_data.model_dump()])

        # Apply Preprocessing
        transformed_data = preprocessor.transform(input_df)

        # Make Prediction
        prediction = int(model.predict(transformed_data)[0])
        probability = float(model.predict_proba(transformed_data)[0][1])

        # Interpret Risk Level
        config_mgr = ConfigurationManager()
        risk_params = config_mgr.get_risk_params_config()

        if probability < risk_params.low_threshold:
            risk_level = "Low"
        elif probability < risk_params.high_threshold:
            risk_level = "Medium"
        else:
            risk_level = "High"

        return PredictionOutput(
            prediction=prediction, probability=probability, risk_level=risk_level
        )

    except Exception as e:
        logger.error(f"Prediction Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Prediction failed due to an internal processing error.",
        )
