"""
Stage 04: Model Trainer Pipeline.

This module coordinates the model training process.
"""

import sys
from src.config.configuration import ConfigurationManager
from src.components.model_trainer import ModelTrainer
from src.utils.logger import get_logger
from src.utils.exception import CustomException

STAGE_NAME = "Model Trainer stage"
logger = get_logger(__name__)


class ModelTrainerTrainingPipeline:
    """
    Orchestrates the Model Trainer stage of the training pipeline.
    """

    def __init__(self):
        pass

    def main(self):
        """
        Executes the model training stage.
        """
        config = ConfigurationManager()
        model_trainer_config = config.get_model_trainer_config()
        model_trainer = ModelTrainer(config=model_trainer_config)
        model_trainer.train()


if __name__ == "__main__":
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        obj = ModelTrainerTrainingPipeline()
        obj.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e
