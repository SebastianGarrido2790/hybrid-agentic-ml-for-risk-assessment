"""
API Endpoints for ACRAS.

Centralizes endpoint business logic for modular expansion.
"""

from fastapi import APIRouter, HTTPException, status, Request
from src.app.schemas import PredictionInput, PredictionOutput
import pandas as pd

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
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
    return {"status": "ok", "service": "ACRAS-API"}


@router.post(
    "/predict", response_model=PredictionOutput, status_code=status.HTTP_200_OK
)
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
        if probability < 0.3:
            risk_level = "Low"
        elif probability < 0.7:
            risk_level = "Medium"
        else:
            risk_level = "High"

        return PredictionOutput(
            prediction=prediction, probability=probability, risk_level=risk_level
        )

    except Exception as e:
        print(f"Prediction Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Prediction failed: {str(e)}",
        )
