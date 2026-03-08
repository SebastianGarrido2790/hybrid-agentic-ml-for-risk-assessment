"""
Stage 01: Data Ingestion Pipeline.

This module coordinates the data ingestion process, interfacing between the
ConfigurationManager and the DataIngestion component.
"""

import sys

from src.components.data_ingestion import DataIngestion
from src.config.configuration import ConfigurationManager
from src.utils.exception import CustomException
from src.utils.logger import get_logger

STAGE_NAME = "Data Ingestion stage"
logger = get_logger(__name__)


class DataIngestionTrainingPipeline:
    """
    Orchestrates the Data Ingestion stage of the training pipeline.
    """

    def __init__(self):
        pass

    def main(self):
        """
        Executes the data ingestion stage.
        """
        config = ConfigurationManager()
        data_ingestion_config = config.get_data_ingestion_config()
        data_ingestion = DataIngestion(config=data_ingestion_config)
        data_ingestion.initiate_data_ingestion()


if __name__ == "__main__":
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        obj = DataIngestionTrainingPipeline()
        obj.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e
