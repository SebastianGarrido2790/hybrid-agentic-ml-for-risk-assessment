"""
Data Ingestion Component.

This module handles the initial stage of the MLOps pipeline:
- Obtaining raw data (via generation or loading).
- Splitting the data into Train, Validation, and Test sets.
- Storing the splits as artifacts for downstream stages.
"""

import os
import pandas as pd
from sklearn.model_selection import train_test_split
from src.entity.config_entity import DataIngestionConfig
from src.config.configuration import ConfigurationManager
from src.utils.logger import get_logger
from src.tools.data_generation.synthetic_data import generate_synthetic_data

logger = get_logger(__name__)


class DataIngestion:
    """
    Handles the ingestion and splitting of data for the ACRAS system.
    """

    def __init__(self, config: DataIngestionConfig):
        """
        Initializes the DataIngestion component with the provided configuration.

        Args:
            config (DataIngestionConfig): The configuration entity containing paths and split ratios.
        """
        self.config = config

    def initiate_data_ingestion(self):
        """
        Executes the data ingestion process:
        1. Loads raw data (generates synthetic data if not found).
        2. Splits data into Train, Validation, and Test sets based on configuration.
        3. Saves the splits to the specified artifacts directory.

        Raises:
            Exception: If any error occurs during the ingestion or splitting process.
        """
        logger.info("Entered the data ingestion method or component")
        try:
            # 1. Get or Generate Data
            raw_path = self.config.local_data_file
            if not os.path.exists(raw_path):
                logger.info("Raw data not found. Generating synthetic data.")
                # Using the extracted tool function
                # TODO: In production, n_samples could be a param in params.yaml
                df = generate_synthetic_data(
                    n_samples=1000, random_seed=self.config.random_state
                )

                # Create raw directory if it doesn't exist (handled by config manager but safe to double check)
                os.makedirs(os.path.dirname(raw_path), exist_ok=True)
                df.to_csv(raw_path, index=False)
            else:
                logger.info(f"Reading raw data from {raw_path}")
                df = pd.read_csv(raw_path)

            logger.info("Read the dataset as dataframe")

            # 2. Perform 3-Way Split (Train / Val / Test)
            logger.info("Initiating 3-way data split")

            # First split: Train vs Temp (Test + Val)
            # Temp size = Test Size + Val Size
            test_val_ratio = self.config.val_size + self.config.test_size

            train_set, temp_set = train_test_split(
                df, test_size=test_val_ratio, random_state=self.config.random_state
            )

            # Second split: Temp -> Val + Test
            # We need to calculate the proportion of Test relative to Temp
            # Example: If Val=0.15, Test=0.15 -> Temp=0.30 -> Test is 0.5 of Temp
            test_ratio_relative = self.config.test_size / test_val_ratio

            val_set, test_set = train_test_split(
                temp_set,
                test_size=test_ratio_relative,
                random_state=self.config.random_state,
            )

            # 3. Save Artifacts
            train_path = self.config.unzip_dir / "train.csv"
            val_path = self.config.unzip_dir / "val.csv"
            test_path = self.config.unzip_dir / "test.csv"

            train_set.to_csv(train_path, index=False, header=True)
            val_set.to_csv(val_path, index=False, header=True)
            test_set.to_csv(test_path, index=False, header=True)

            logger.info(f"Ingestion completed. Files saved to {self.config.unzip_dir}")
            logger.info(
                f"Train Shape: {train_set.shape}, Val Shape: {val_set.shape}, Test Shape: {test_set.shape}"
            )

        except Exception as e:
            logger.error(f"Error in data ingestion: {str(e)}")
            raise e


if __name__ == "__main__":
    try:
        config_manager = ConfigurationManager()
        data_ingestion_config = config_manager.get_data_ingestion_config()
        data_ingestion = DataIngestion(config=data_ingestion_config)
        data_ingestion.initiate_data_ingestion()
    except Exception as e:
        logger.error(e)
