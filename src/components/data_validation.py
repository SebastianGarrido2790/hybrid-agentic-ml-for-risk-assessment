"""
Data Validation Component.

This module handles the validation of the ingested data against the defined schema:
- Checks if all columns in the dataset exist in the schema.
- Validates the integrity of the ingested data against the defined schema.
"""

import pandas as pd
import sys
from src.entity.config_entity import DataValidationConfig
from src.utils.logger import get_logger
from src.utils.exception import CustomException

logger = get_logger(__name__)


class DataValidation:
    """
    Validates the integrity of the ingested data against the defined schema.
    """

    def __init__(self, config: DataValidationConfig):
        self.config = config

    def validate_all_columns(self) -> bool:
        """
        Checks if all columns in the dataset exist in the schema.

        Returns:
            bool: True if validation passes, False otherwise.
        """
        try:
            validation_status = True

            # Read the training data for validation
            data_path = self.config.unzip_data_dir / "train.csv"
            data = pd.read_csv(data_path)
            all_cols = list(data.columns)

            all_schema = self.config.all_schema.keys()

            with open(self.config.STATUS_FILE, "w") as f:
                for col in all_cols:
                    if col not in all_schema:
                        validation_status = False
                        logger.error(f"Column {col} not found in schema.")
                        f.write(f"Validation status: {validation_status}\n")
                        f.write(f"Column {col} not in schema.\n")
                        return validation_status

                # Check if all schema columns are in data (optional but good practice)
                for col in all_schema:
                    if col not in all_cols:
                        validation_status = False
                        # It's okay if target is missing for inference, but for training data it should be there.
                        logger.error(f"Schema column {col} not found in data.")
                        f.write(f"Validation status: {validation_status}\n")
                        f.write(f"Schema column {col} not in data.\n")
                        return validation_status

                f.write(f"Validation status: {validation_status}")
                logger.info(f"Data validation status: {validation_status}")

            return validation_status

        except Exception as e:
            raise CustomException(e, sys)
