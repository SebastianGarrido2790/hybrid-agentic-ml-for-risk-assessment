"""
Unit Tests for DataTransformation Component.

Tests the creation of the ColumnTransformer object and the execution
of the transformation pipeline (fitting and transforming data splits).
"""

import pytest
import pandas as pd
from unittest.mock import patch
from pathlib import Path
from sklearn.compose import ColumnTransformer
from src.components.data_transformation import DataTransformation
from src.entity.config_entity import DataTransformationConfig


@pytest.fixture
def data_transformation_config():
    return DataTransformationConfig(
        root_dir=Path("artifacts/data_transformation"),
        data_path=Path("artifacts/data_ingestion"),
        preprocessor_path=Path("artifacts/data_transformation/preprocessor.pkl"),
    )


def test_get_data_transformer_object(data_transformation_config):
    transformation = DataTransformation(config=data_transformation_config)
    # Mocking instance variables that are usually set in initiate_data_transformation
    transformation.numerical_cols = ["num1"]
    transformation.categorical_cols = ["cat1"]
    transformation.cols_to_drop = []

    preprocessor = transformation.get_data_transformer_object()
    assert isinstance(preprocessor, ColumnTransformer)


@patch("src.components.data_transformation.pd.read_csv")
@patch("src.components.data_transformation.joblib.dump")
def test_initiate_data_transformation(
    mock_dump, mock_read_csv, data_transformation_config
):
    # Setup
    transformation = DataTransformation(config=data_transformation_config)

    # Mock DataFrames
    # Need numeric and categorical columns to match logic
    df = pd.DataFrame(
        {
            "id_empresa": [1, 2],  # Dropped
            "ano": [2022, 2022],  # Dropped
            "default_probability": [0.1, 0.2],  # Dropped
            "num1": [10.0, 20.0],
            "target": [0, 1],
        }
    )
    mock_read_csv.side_effect = [df, df, df]  # train, val, test

    # Execute
    # We need to spy on preprocessor fit/transform or just verify output file creation
    # Since verifying file creation involves mocking to_csv on the dataframe created INSIDE the method
    # It's slightly complex. We will trust the flow if no exceptions and joblib dump is called.

    # We need to patch pd.DataFrame.to_csv to avoid writing to disk
    with patch("pandas.DataFrame.to_csv") as mock_to_csv:
        transformation.initiate_data_transformation()

    # Verify
    assert mock_dump.called  # Preprocessor saved
    assert mock_to_csv.call_count == 3  # Train, Val, Test saved

    # Verify cols
    assert transformation.numerical_cols == ["num1"]
    assert transformation.categorical_cols == []
