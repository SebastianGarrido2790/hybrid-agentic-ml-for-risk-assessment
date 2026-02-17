"""
Unit Tests for ModelTrainer Component.

Tests the model training process, including hyperparameter usage,
training execution on prepared data, and artifact persistence.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.components.model_trainer import ModelTrainer
from src.entity.config_entity import ModelTrainerConfig


@pytest.fixture
def model_trainer_config():
    return ModelTrainerConfig(
        root_dir=Path("artifacts/model_trainer"),
        train_data_path=Path("artifacts/data_transformation/train.csv"),
        val_data_path=Path("artifacts/data_transformation/val.csv"),
        model_name="model.joblib",
        n_estimators=10,
        min_samples_leaf=2,
        class_weight="balanced",
        n_jobs=-1,
        random_state=42,
    )


@patch("src.components.model_trainer.pd.read_csv")
@patch("src.components.model_trainer.joblib.dump")
@patch("src.components.model_trainer.RandomForestClassifier")
def test_train_model(mock_rf, mock_dump, mock_read_csv, model_trainer_config):
    # Setup
    trainer = ModelTrainer(config=model_trainer_config)

    mock_df = pd.DataFrame({"feat1": [1, 2], "target": [0, 1]})
    mock_read_csv.return_value = mock_df

    mock_model_instance = MagicMock()
    mock_rf.return_value = mock_model_instance

    # Execute
    trainer.train()

    # Verify
    mock_rf.assert_called_with(
        n_estimators=10,
        min_samples_leaf=2,
        class_weight="balanced",
        n_jobs=-1,
        random_state=42,
    )
    mock_model_instance.fit.assert_called()
    assert mock_dump.called
    args, _ = mock_dump.call_args
    # First arg is model, second is path
    assert args[0] == mock_model_instance
    # Path comparison depends on OS, ensure it ends with model name
    assert str(args[1]).endswith("model.joblib")
