"""
FastAPI Test Fixtures.

Provides fixtures specifically for testing the Prediction Service, including
mocked ML models and preprocessors to simulate app state without loading real artifacts.
"""

import pytest
from unittest.mock import MagicMock
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
from src.app.main import app


@pytest.fixture
def mock_model():
    model = MagicMock()
    model.predict.return_value = [0]
    model.predict_proba.return_value = [[0.8, 0.2]]
    return model


@pytest.fixture
def mock_preprocessor():
    prep = MagicMock()
    # Mock transform to return some dummy array
    prep.transform.return_value = [[0.1, 0.2]]
    return prep


@pytest.fixture
def client(mock_model, mock_preprocessor):
    # Override lifespan to mock startup
    @asynccontextmanager
    async def mock_lifespan(app):
        app.state.model = mock_model
        app.state.preprocessor = mock_preprocessor
        yield
        app.state.model = None
        app.state.preprocessor = None

    app.router.lifespan_context = mock_lifespan

    with TestClient(app) as c:
        yield c
