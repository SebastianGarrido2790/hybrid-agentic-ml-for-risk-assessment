"""
Component: Data Augmentation.

This module uses the Synthetic Data Generator tool to ensure a balanced dataset
before the main ingestion pipeline runs. It implements the 'Agentic Healing'
philosophy by fixing data imbalance autonomously.
"""

import os
import shutil
import sys

import pandas as pd

from src.entity.config_entity import DataAugmentationConfig
from src.tools.synthetic_data_generator import generate_synthetic_data
from src.utils.exception import CustomException
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataAugmentation:
    """
    Component for orchestrating data augmentation using synthetic generation.
    """

    def __init__(self, config: DataAugmentationConfig):
        self.config = config

    def initiate_data_augmentation(self) -> None:
        """
        Loads raw data, generates synthetic samples, and saves combined data to processed.
        """
        try:
            raw_fin_path = os.path.join(
                self.config.raw_data_dir, "financial_statements_training.csv"
            )
            raw_pd_path = os.path.join(self.config.raw_data_dir, "pd_training.csv")
            processed_dir = self.config.processed_data_dir

            os.makedirs(processed_dir, exist_ok=True)

            if not os.path.exists(raw_fin_path) or not os.path.exists(raw_pd_path):
                logger.warning("Raw data not found. Skipping augmentation.")
                return

            logger.info(f"Loading raw data from {raw_fin_path}")
            df_fin_raw = pd.read_csv(raw_fin_path)
            df_pd_raw = pd.read_csv(raw_pd_path)

            logger.info("Generating synthetic samples for class balance...")
            syn_fin, syn_pd = generate_synthetic_data(self.config.n_samples)

            logger.info("Combining original and synthetic data...")
            df_fin_combined = pd.concat([df_fin_raw, syn_fin], ignore_index=True)
            df_pd_combined = pd.concat([df_pd_raw, syn_pd], ignore_index=True)

            proc_fin_path = os.path.join(
                processed_dir, "financial_statements_training.csv"
            )
            proc_pd_path = os.path.join(processed_dir, "pd_training.csv")

            logger.info(f"Saving augmented dataset to {processed_dir}")
            df_fin_combined.to_csv(proc_fin_path, index=False)
            df_pd_combined.to_csv(proc_pd_path, index=False)

            # Copy validation data to processed as well for ingestion consistency
            for val_file in [
                "financial_statements_validation.csv",
                "pd_validation.csv",
            ]:
                val_raw = os.path.join(self.config.raw_data_dir, val_file)
                val_proc = os.path.join(processed_dir, val_file)
                if os.path.exists(val_raw):
                    shutil.copy(val_raw, val_proc)

        except Exception as e:
            raise CustomException(e, sys)
