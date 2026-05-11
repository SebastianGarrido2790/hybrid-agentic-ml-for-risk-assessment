"""
Unit tests for Data Augmentation component.
"""

import os
from unittest.mock import patch

import pandas as pd
import pytest

from src.components.data_augmentation import DataAugmentation
from src.entity.config_entity import DataAugmentationConfig


@pytest.fixture
def augmentation_config(tmp_path):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()

    # Create mock raw files
    pd.DataFrame({"id_empresa": [1], "ingresos": [100]}).to_csv(
        raw_dir / "financial_statements_training.csv", index=False
    )
    pd.DataFrame({"id_empresa": [1], "default_prob": [0.1]}).to_csv(
        raw_dir / "pd_training.csv", index=False
    )

    return DataAugmentationConfig(
        root_dir=tmp_path,
        raw_data_dir=raw_dir,
        processed_data_dir=processed_dir,
        n_samples=5,
    )


def test_initiate_data_augmentation_success(augmentation_config):
    """Test successful augmentation process."""
    mock_syn_fin = pd.DataFrame({"id_empresa": [2], "ingresos": [200]})
    mock_syn_pd = pd.DataFrame({"id_empresa": [2], "default_prob": [0.2]})

    with patch(
        "src.components.data_augmentation.generate_synthetic_data",
        return_value=(mock_syn_fin, mock_syn_pd),
    ):
        augmentation = DataAugmentation(augmentation_config)
        augmentation.initiate_data_augmentation()

        # Check if files were created in processed dir
        proc_fin_path = os.path.join(
            augmentation_config.processed_data_dir, "financial_statements_training.csv"
        )
        proc_pd_path = os.path.join(
            augmentation_config.processed_data_dir, "pd_training.csv"
        )

        assert os.path.exists(proc_fin_path)
        assert os.path.exists(proc_pd_path)

        df_fin = pd.read_csv(proc_fin_path)
        assert len(df_fin) == 2  # 1 original + 1 synthetic


def test_initiate_data_augmentation_skip(tmp_path):
    """Test skipping if raw data is missing."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    processed_dir = tmp_path / "proc"

    config = DataAugmentationConfig(
        root_dir=tmp_path,
        raw_data_dir=empty_dir,
        processed_data_dir=processed_dir,
        n_samples=5,
    )

    augmentation = DataAugmentation(config)
    augmentation.initiate_data_augmentation()

    # Files should NOT exist
    proc_fin_path = os.path.join(processed_dir, "financial_statements_training.csv")
    assert not os.path.exists(proc_fin_path)
