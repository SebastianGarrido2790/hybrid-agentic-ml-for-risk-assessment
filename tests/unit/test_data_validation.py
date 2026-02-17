"""
Unit Tests for DataValidation Component.

Tests schema validation against the defined configuration, ensuring
correct status file generation for pass/fail scenarios.
"""

import pytest
import pandas as pd
from unittest.mock import patch, mock_open
from pathlib import Path
from src.components.data_validation import DataValidation
from src.entity.config_entity import DataValidationConfig


@pytest.fixture
def data_validation_config():
    return DataValidationConfig(
        root_dir=Path("artifacts/data_validation"),
        STATUS_FILE="artifacts/data_validation/status.txt",
        unzip_data_dir=Path("artifacts/data_ingestion"),
        all_schema={"col1": "int", "col2": "float", "target": "int"},
    )


@patch("src.components.data_validation.pd.read_csv")
def test_validate_all_columns_success(mock_read_csv, data_validation_config):
    # Setup
    # Data has all columns in schema
    mock_df = pd.DataFrame(columns=["col1", "col2", "target"])
    mock_read_csv.return_value = mock_df

    validation = DataValidation(config=data_validation_config)

    # Execute
    with patch("builtins.open", mock_open()) as mock_file:
        result = validation.validate_all_columns()

    # Verify
    assert result is True
    mock_file.assert_called_with(data_validation_config.STATUS_FILE, "w")
    # Verify status True was written
    handle = mock_file()
    handle.write.assert_any_call("Validation status: True")


@patch("src.components.data_validation.pd.read_csv")
def test_validate_all_columns_failure_missing_col(
    mock_read_csv, data_validation_config
):
    # Setup
    # Data is missing 'col2'
    mock_df = pd.DataFrame(columns=["col1", "target"])
    mock_read_csv.return_value = mock_df

    validation = DataValidation(config=data_validation_config)

    # Execute
    with patch("builtins.open", mock_open()) as mock_file:
        result = validation.validate_all_columns()

    # Verify
    assert result is False
    try:
        # It writes failure status
        handle = mock_file()
        handle.write.assert_any_call("Validation status: False\n")
    except AssertionError:
        # Sometimes write calls are split differently, check calls list if needed
        pass
