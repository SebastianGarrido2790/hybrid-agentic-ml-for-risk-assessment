"""
Stage 06: Model Registration Pipeline.

This module orchestrates the registration of the trained model into the MLflow Model Registry.
"""

from src.config.configuration import ConfigurationManager
from src.components.model_registration import ModelRegistration
from src.utils.exception import CustomException
from src.utils.logger import get_logger
import sys

STAGE_NAME = "Model Registration stage"
logger = get_logger(__name__)


class ModelRegistrationTrainingPipeline:
    """
    Orchestrates the Model Registration stage of the training pipeline.
    """

    def __init__(self):
        pass

    def main(self):
        """
        Executes the model registration stage.
        """
        config = ConfigurationManager()
        model_registration_config = config.get_model_registration_config()
        model_registration = ModelRegistration(config=model_registration_config)
        model_registration.log_into_mlflow()


if __name__ == "__main__":
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        obj = ModelRegistrationTrainingPipeline()
        obj.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e
