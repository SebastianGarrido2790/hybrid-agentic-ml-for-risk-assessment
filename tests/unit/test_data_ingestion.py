"""
Unit Tests for DataIngestion Component.

Tests the data loading, merging, feature engineering integration,
and stratified train-test splitting logic.
"""

import pytest
import pandas as pd
from unittest.mock import patch
from pathlib import Path
from src.components.data_ingestion import DataIngestion
from src.entity.config_entity import DataIngestionConfig


@pytest.fixture
def data_ingestion_config():
    return DataIngestionConfig(
        root_dir=Path("artifacts/data_ingestion"),
        source_data_dir=Path("data/raw"),
        financial_data_file="financials.csv",
        pd_data_file="pd.csv",
        unzip_dir=Path("artifacts/data_ingestion"),
        test_size=0.2,
        val_size=0.2,
        random_state=42,
        target_column="custom_target",
    )


@patch("src.components.data_ingestion.pd.read_csv")
@patch("src.components.data_ingestion.os.path.exists")
def test_load_and_merge_raw_data(
    mock_exists,
    mock_read_csv,
    data_ingestion_config,
    sample_financial_data,
    sample_pd_data,
):
    mock_exists.return_value = True
    # Side effect for read_csv to return financial data then pd data
    mock_read_csv.side_effect = [sample_financial_data, sample_pd_data]

    ingestion = DataIngestion(config=data_ingestion_config)
    merged_df = ingestion._load_and_merge_raw_data("fin_path", "pd_path")

    # Verify ID 1 is merged (intersection) and unique per company
    assert len(merged_df) == 3
    # ID 1 should be present once
    assert merged_df[merged_df["id_empresa"] == 1].shape[0] == 1
    # Check aggregation logic: ID 1 ebitda should be 200 (latest year 2022)
    assert merged_df[merged_df["id_empresa"] == 1]["ebitda"].values[0] == 200
    # Check PD aggregation: ID 1 risk_score should be mean(10, 12) = 11
    assert merged_df[merged_df["id_empresa"] == 1]["risk_score"].values[0] == 11.0


@patch("src.components.data_ingestion.DataIngestion._load_and_merge_raw_data")
@patch("src.components.data_ingestion.engineer_features")
@patch("src.components.data_ingestion.train_test_split")
@patch("src.components.data_ingestion.os.makedirs")
def test_initiate_data_ingestion(
    mock_makedirs,
    mock_train_test_split,
    mock_engineer_features,
    mock_load_merge,
    data_ingestion_config,
):
    # Setup
    ingestion = DataIngestion(config=data_ingestion_config)

    # Mock return values
    mock_df = pd.DataFrame({"id": [1, 2, 3], "target": [0, 1, 0]})
    mock_load_merge.return_value = mock_df
    mock_engineer_features.return_value = mock_df

    # Mock split: simple passthrough for testing flow
    # First split: train, temp
    mock_train_test_split.side_effect = [
        (mock_df, mock_df),  # First split
        (mock_df, mock_df),  # Second split
    ]

    # Execute
    ingestion.initiate_data_ingestion()

    # Verify
    assert mock_load_merge.call_count == 2  # Once for train, once for val raw paths
    assert mock_engineer_features.call_count == 2
    assert mock_train_test_split.call_count == 2
    assert mock_makedirs.called

    # Ideally should mock to_csv but sticking to high level connection logic
