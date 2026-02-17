"""
Main Application for the ACRAS Prediction Service.

This FastAPI application exposes the trained machine learning model as a REST API.
It handles:
- Model Loading (via Lifespan events)
- Health Checks
- Prometheus Metrics Instrumentation
- Prediction Requests
"""

from fastapi import FastAPI
from src.app.api.endpoints import router as api_router
from src.config.configuration import ConfigurationManager
import joblib
from contextlib import asynccontextmanager
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator

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
        import traceback

        traceback.print_exc()
        print(f"CRITICAL ERROR loading artifacts: {e}")
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


if __name__ == "__main__":
    # For local debugging
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)
