"""
Unit tests for the Model Registration component.

This module tests the logic for registering trained models in the
MLflow Model Registry based on performance thresholds.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.components.model_registration import ModelRegistration
from src.entity.config_entity import ModelRegistrationConfig


@pytest.fixture
def mock_registration_config():
    """
    Provides a mock configuration for ModelRegistration.
    """
    return ModelRegistrationConfig(
        root_dir=Path("artifacts/model_registration"),
        model_path=Path("artifacts/model_trainer/model.joblib"),
        metric_file_name=Path("artifacts/model_evaluation/metrics.json"),
        model_name="test_model",
        mlflow_uri="file:./mlruns",
        min_roc_auc=0.5,
    )


@patch("src.components.model_registration.joblib.load")
@patch("src.components.model_registration.json.load")
@patch("src.components.model_registration.mlflow")
def test_register_model(
    mock_mlflow, mock_json_load, mock_joblib_load, mock_registration_config
):
    # Setup mock
    mock_model = MagicMock()
    mock_joblib_load.return_value = mock_model

    mock_json_load.return_value = {"accuracy": 0.9, "roc_auc": 0.8}

    registration = ModelRegistration(config=mock_registration_config)

    with (
        patch("builtins.open", MagicMock()),
        patch("pathlib.Path.exists", return_value=True),
    ):
        registration.log_into_mlflow()

    mock_mlflow.log_metrics.assert_called_once_with({"accuracy": 0.9, "roc_auc": 0.8})
