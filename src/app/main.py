"""
Main Application for the ACRAS Prediction Service.

This FastAPI application exposes the trained machine learning model as a REST API.
It handles:
- Model Loading (via Lifespan events)
- Health Checks
- Prometheus Metrics Instrumentation
- Prediction Requests

Usage:
- Option 1: Using the python module (production-like)
    uv run python -m src.app.main

- Option 2: Using uvicorn with auto-reload (development)
    uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from contextlib import asynccontextmanager

import joblib
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from src.utils.logger import get_logger

from src.app.api.endpoints import router as api_router
from src.config.configuration import ConfigurationManager

logger = get_logger(__name__, headline="main.py")

# Global variables for model and preprocessor NO LONGER USED
# State is stored in app.state


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for loading the model and preprocessor on startup.
    This ensures we only load artifacts once, not per request.
    """
    try:
        config = ConfigurationManager()

        # Load Model
        # In a real scenario, we might want to load from the Registry (models:/...)
        # but for simplicity/speed we load the specific artifact defined in config
        model_path = config.get_model_evaluation_config().model_path
        app.state.model = joblib.load(model_path)

        preprocessor_path = config.get_data_transformation_config().preprocessor_path
        app.state.preprocessor = joblib.load(preprocessor_path)

        yield
    except Exception as e:
        logger.critical(f"CRITICAL ERROR loading artifacts: {e}", exc_info=True)
        # Build might fail if artifacts are missing, which is expected behavior for a container checks
        raise e
    finally:
        # Clean up resources if needed
        pass


app = FastAPI(
    title="ACRAS Prediction Service",
    description="Agentic Credit Risk Assessment System API",
    lifespan=lifespan,
)

# Instrument Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Include Router
app.include_router(api_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to prevent internal stack trace leakage.
    Logs the full error internally and returns a generic 500 response.
    """
    logger.critical(f"Unhandled Exception at {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact support."},
    )


if __name__ == "__main__":
    # For local debugging
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)
