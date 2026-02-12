"""
Stage 02: Data Transformation Pipeline.

This module coordinates the data transformation process, interfacing between the
ConfigurationManager and the DataTransformation component.
"""

from src.config.configuration import ConfigurationManager
from src.components.data_transformation import DataTransformation
from src.utils.logger import get_logger

STAGE_NAME = "Data Transformation stage"
logger = get_logger(__name__)


class DataTransformationTrainingPipeline:
    """
    Orchestrates the Data Transformation stage of the training pipeline.
    """

    def __init__(self):
        pass

    def main(self):
        """
        Executes the data transformation stage.
        """
        config_manager = ConfigurationManager()
        data_transformation_config = config_manager.get_data_transformation_config()
        data_transformation = DataTransformation(config=data_transformation_config)
        data_transformation.initiate_data_transformation()


if __name__ == "__main__":
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        obj = DataTransformationTrainingPipeline()
        obj.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.exception(e)
        raise e
