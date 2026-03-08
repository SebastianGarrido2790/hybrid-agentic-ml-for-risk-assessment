"""
Stage 05: Model Evaluation Pipeline.

This module orchestrates the evaluation of the trained model,
leveraging the ModelEvaluation component and MLflow for tracking.
"""

import sys

from src.components.model_evaluation import ModelEvaluation
from src.config.configuration import ConfigurationManager
from src.utils.exception import CustomException
from src.utils.logger import get_logger

STAGE_NAME = "Model Evaluation stage"
logger = get_logger(__name__)


class ModelEvaluationTrainingPipeline:
    """
    Orchestrates the model evaluation stage of the pipeline.
    """

    def __init__(self):
        """
        Initializes the pipeline stage.
        """
        pass

    def main(self):
        """
        Executes the model evaluation logic:
        1. Loads the configuration.
        2. Initializes the ModelEvaluation component.
        3. Calculates and logs metrics.
        """
        config = ConfigurationManager()
        model_evaluation_config = config.get_model_evaluation_config()
        model_evaluation = ModelEvaluation(config=model_evaluation_config)
        model_evaluation.log_into_mlflow()


if __name__ == "__main__":
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        obj = ModelEvaluationTrainingPipeline()
        obj.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e
