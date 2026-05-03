"""
Stage 00: Data Augmentation Pipeline.

This stage ensures the dataset is balanced and sufficient before the main
ingestion process begins.
"""

import sys

from src.components.data_augmentation import DataAugmentation
from src.config.configuration import ConfigurationManager
from src.utils.exception import CustomException
from src.utils.logger import get_logger

STAGE_NAME = "Data Augmentation stage"
logger = get_logger(__name__)


class DataAugmentationTrainingPipeline:
    """
    Orchestrates the Data Augmentation stage.
    """

    def __init__(self):
        pass

    def main(self):
        """
        Executes the data augmentation stage.
        """
        config = ConfigurationManager()
        augmentation_config = config.get_data_augmentation_config()
        augmentation = DataAugmentation(config=augmentation_config)
        augmentation.initiate_data_augmentation()


if __name__ == "__main__":
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        obj = DataAugmentationTrainingPipeline()
        obj.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e
