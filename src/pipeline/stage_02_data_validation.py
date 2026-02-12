"""
Stage 02: Data Validation Pipeline.

This module coordinates the data validation process, ensuring data integrity
before proceeding to transformation.
"""

import sys
from src.config.configuration import ConfigurationManager
from src.components.data_validation import DataValidation
from src.utils.logger import get_logger
from src.utils.exception import CustomException

STAGE_NAME = "Data Validation stage"
logger = get_logger(__name__)


class DataValidationTrainingPipeline:
    """
    Orchestrates the Data Validation stage of the training pipeline.
    """

    def __init__(self):
        pass

    def main(self):
        """
        Executes the data validation stage.
        """
        config = ConfigurationManager()
        data_validation_config = config.get_data_validation_config()
        data_validation = DataValidation(config=data_validation_config)
        data_validation.validate_all_columns()


if __name__ == "__main__":
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        obj = DataValidationTrainingPipeline()
        obj.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e
