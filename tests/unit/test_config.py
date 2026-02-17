"""
Unit Tests for ConfigurationManager.

Tests the loading and parsing of YAML configurations into typed entity objects.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.config.configuration import ConfigurationManager
from src.entity.config_entity import DataIngestionConfig


@pytest.fixture
def mock_config_response():
    config = MagicMock()
    config.artifacts_root = "artifacts"
    config.data_ingestion.root_dir = "artifacts/data_ingestion"
    config.data_ingestion.source_data_dir = "data/raw"
    config.data_ingestion.financial_data_file = "financials.csv"
    config.data_ingestion.pd_data_file = "pd.csv"
    config.data_ingestion.unzip_dir = "artifacts/data_ingestion"
    return config


@pytest.fixture
def mock_params_response():
    params = MagicMock()
    params.data_split.test_size = 0.2
    params.data_split.val_size = 0.2
    params.data_split.random_state = 42
    return params


@pytest.fixture
def mock_schema_response():
    schema = MagicMock()
    schema.target_column = "target"
    return schema


@patch("src.config.configuration.read_yaml")
@patch("src.config.configuration.create_directories")
def test_get_data_ingestion_config(
    mock_create_directories,
    mock_read_yaml,
    mock_config_response,
    mock_params_response,
    mock_schema_response,
):
    # Setup mocks to return different values based on input path
    # logic to differentiate between config, params, schema reads
    # simpler verify: verify attributes are properly mapped.
    mock_read_yaml.side_effect = [
        mock_config_response,
        mock_params_response,
        mock_schema_response,
    ]

    config_manager = ConfigurationManager()
    ingestion_config = config_manager.get_data_ingestion_config()

    assert isinstance(ingestion_config, DataIngestionConfig)
    assert ingestion_config.root_dir == Path("artifacts/data_ingestion")
    assert ingestion_config.test_size == 0.2
    assert ingestion_config.random_state == 42
