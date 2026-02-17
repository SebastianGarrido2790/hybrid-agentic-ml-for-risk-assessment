"""
Integration Tests for Pipeline Stages.

Verifies the correct handoff of data artifacts between pipeline components,
specifically ensuring the Data Ingestion output is correctly consumed by Data Validation.
"""

import pytest
from src.components.data_ingestion import DataIngestion
from src.components.data_validation import DataValidation
from src.entity.config_entity import DataIngestionConfig, DataValidationConfig


@pytest.fixture
def integration_test_dirs(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    ingestion_dir = artifacts_dir / "data_ingestion"
    ingestion_dir.mkdir()
    validation_dir = artifacts_dir / "data_validation"
    validation_dir.mkdir()

    return source_dir, artifacts_dir, ingestion_dir, validation_dir


def test_ingestion_validation_integration(
    integration_test_dirs, sample_financial_data, sample_pd_data
):
    # Setup
    source_dir, artifacts_dir, ingestion_dir, validation_dir = integration_test_dirs

    # Create dummy raw data
    fin_path = source_dir / "financials.csv"
    pd_path = source_dir / "pd.csv"
    sample_financial_data.to_csv(fin_path, index=False)
    sample_pd_data.to_csv(pd_path, index=False)

    # 1. Run Data Ingestion
    ingestion_config = DataIngestionConfig(
        root_dir=ingestion_dir,
        source_data_dir=source_dir,
        financial_data_file="financials.csv",
        pd_data_file="pd.csv",
        unzip_dir=ingestion_dir,
        test_size=0.2,
        val_size=0.2,
        random_state=42,
        target_column="target",  # Doesn't matter for this test as we mocking/using sample data which might not have it
    )

    # Patching feature engineering to avoid complexity of real engineering logic
    # We just want to ensure file flow
    from unittest.mock import patch

    with patch("src.components.data_ingestion.engineer_features") as mock_eng:
        # Mock engineer to just return the merged dataframe with a dummy target
        def side_effect(df):
            df["target"] = 0
            return df

        mock_eng.side_effect = side_effect

        ingestion = DataIngestion(config=ingestion_config)
        ingestion.initiate_data_ingestion()

    # Verify Ingestion Output
    train_path = ingestion_dir / "train.csv"
    assert train_path.exists()

    # 2. Run Data Validation using Ingestion Output
    validation_config = DataValidationConfig(
        root_dir=validation_dir,
        STATUS_FILE=validation_dir / "status.txt",
        unzip_data_dir=ingestion_dir,  # Pointing to ingestion output
        all_schema={
            "target": "int",
            "id_empresa": "int",
            "ano": "int",
            "ingresos": "float",
            "ebitda": "float",
            "default_prob": "float",
            "risk_score": "float",
        },  # Schema matching ingestion output
    )

    validation = DataValidation(config=validation_config)
    result = validation.validate_all_columns()

    # Verify Validation Result
    assert result is True
    assert (validation_dir / "status.txt").exists()

    # Check if status file says True
    with open(validation_dir / "status.txt", "r") as f:
        content = f.read()
        assert "Validation status: True" in content
