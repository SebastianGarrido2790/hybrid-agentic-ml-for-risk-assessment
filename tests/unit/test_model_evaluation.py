"""
Unit tests for the Model Evaluation component.

This module tests the logic for calculating metrics and logging
evaluation results to MLflow.
"""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.components.model_evaluation import ModelEvaluation
from src.entity.config_entity import ModelEvaluationConfig


@pytest.fixture
def mock_evaluation_config():
    """
    Provides a mock configuration for ModelEvaluation.
    """
    return ModelEvaluationConfig(
        root_dir=Path("artifacts/model_evaluation"),
        test_data_path=Path("artifacts/data_transformation/test.csv"),
        model_path=Path("artifacts/model_trainer/model.joblib"),
        all_params={"n_estimators": 100},
        metric_file_name=Path("artifacts/model_evaluation/metrics.json"),
        target_column="target",
        mlflow_uri="file:./mlruns",
        experiment_name="test_experiment",
        registered_model_name="test_model",
        mlflow_model_name="test_model_dir",
    )


@patch("src.components.model_evaluation.pd.read_csv")
@patch("src.components.model_evaluation.joblib.load")
@patch("src.components.model_evaluation.mlflow")
def test_evaluate_model(
    mock_mlflow, mock_joblib_load, mock_read_csv, mock_evaluation_config
):
    # Setup test data
    mock_df = pd.DataFrame({"feature1": [1.0, 2.0], "target": [0, 1]})
    mock_read_csv.return_value = mock_df

    # Setup real model to avoid mlflow serialization issues
    model = LogisticRegression()
    X = np.array([[1.0], [2.0]])
    y = np.array([0, 1])
    model.fit(X, y)

    mock_joblib_load.return_value = model

    # Instantiate
    evaluation = ModelEvaluation(config=mock_evaluation_config)
    mock_mlflow.get_tracking_uri.return_value = "file:./mlruns"

    with (
        patch("src.components.model_evaluation.save_json") as mock_save_json,
        patch("pathlib.Path.exists", return_value=True),
    ):
        evaluation.log_into_mlflow()

    mock_save_json.assert_called_once()
    mock_mlflow.log_metrics.assert_called_once()
