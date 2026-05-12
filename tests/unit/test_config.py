"""
Unit Tests for ConfigurationManager.

Tests the loading and parsing of YAML configurations into typed entity objects.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.config.configuration import ConfigurationManager
from src.entity.config_entity import DataIngestionConfig


@pytest.fixture
def mock_config_dict():
    return {
        "artifacts_root": "artifacts",
        "data_ingestion": {
            "root_dir": "artifacts/data_ingestion",
            "source_data_dir": "data/raw",
            "financial_data_file": "financials.csv",
            "pd_data_file": "pd.csv",
            "unzip_dir": "artifacts/data_ingestion",
        },
        "data_augmentation": {
            "root_dir": "artifacts/data_augmentation",
            "raw_data_dir": "data/raw",
            "processed_data_dir": "data/processed",
        },
        "data_validation": {
            "root_dir": "artifacts/data_validation",
            "unzip_data_dir": "artifacts/data_ingestion",
            "STATUS_FILE": "artifacts/data_validation/status.txt",
            "EXPECTATIONS_FILE": "artifacts/data_validation/expectations.json",
        },
        "data_transformation": {
            "root_dir": "artifacts/data_transformation",
            "data_path": "artifacts/data_ingestion",
            "preprocessor_path": "artifacts/data_transformation/preprocessor.pkl",
            "cols_to_drop": ["id", "target"],
        },
        "model_trainer": {
            "root_dir": "artifacts/model_trainer",
            "train_data_path": "artifacts/data_transformation/train.csv",
            "val_data_path": "artifacts/data_transformation/val.csv",
            "model_name": "acras_rf_model.joblib",
        },
        "model_evaluation": {
            "root_dir": "artifacts/model_evaluation",
            "test_data_path": "artifacts/data_transformation/test.csv",
            "model_path": "artifacts/model_trainer/acras_rf_model.joblib",
            "metric_file_name": "artifacts/model_evaluation/metrics.json",
            "experiment_name": "ACRAS_Risk_Assessment",
            "registered_model_name": "ACRAS_RandomForest_v1",
            "mlflow_model_name": "acras_risk_model",
        },
        "model_registration": {
            "root_dir": "artifacts/model_registration",
            "model_path": "artifacts/model_trainer/acras_rf_model.joblib",
            "metric_file_name": "artifacts/model_evaluation/metrics.json",
            "model_name": "ACRAS_RandomForest_v1",
        },
    }


@pytest.fixture
def mock_params_dict():
    return {
        "data_split": {"test_size": 0.2, "val_size": 0.2, "random_state": 42},
        "model_params": {
            "n_estimators": 100,
            "min_samples_leaf": 5,
            "class_weight": "balanced",
            "n_jobs": -1,
        },
        "mlflow": {"uri": "http://127.0.0.1:5000"},
        "registration_params": {"min_roc_auc": 0.60},
        "augmentation": {"n_samples": 100},
        "risk_thresholds": {
            "low": 0.3,
            "high": 0.7,
            "mora_critical": 0.2,
            "current_ratio_critical": 0.5,
        },
        "feature_params": {"insolvent_cap": 10.0},
    }


@pytest.fixture
def mock_schema_dict():
    return {"target_column": "target", "columns": {"id": "int64", "target": "int64"}}


@patch("src.config.configuration.read_yaml")
@patch("src.config.configuration.create_directories")
def test_get_data_ingestion_config(
    mock_create_directories,
    mock_read_yaml,
    mock_config_dict,
    mock_params_dict,
    mock_schema_dict,
):
    # Setup mocks to return different values based on input path
    mock_read_yaml.side_effect = [
        mock_config_dict,
        mock_params_dict,
        mock_schema_dict,
    ]

    config_manager = ConfigurationManager()
    ingestion_config = config_manager.get_data_ingestion_config()

    assert isinstance(ingestion_config, DataIngestionConfig)
    assert ingestion_config.root_dir == Path("artifacts/data_ingestion")
    assert ingestion_config.test_size == 0.2
    assert ingestion_config.random_state == 42
