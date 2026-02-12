"""
Main entry point for the Agentic Credit Risk Assessment System (ACRAS) pipeline.

This script allows for manual orchestration of the pipeline stages for debugging
and development purposes.

Usage:
    uv run python main.py
"""

import sys
from src.pipeline.stage_01_data_ingestion import DataIngestionTrainingPipeline
from src.pipeline.stage_02_data_validation import DataValidationTrainingPipeline
from src.pipeline.stage_03_data_transformation import DataTransformationTrainingPipeline
from src.pipeline.stage_04_model_trainer import ModelTrainerTrainingPipeline
from src.pipeline.stage_05_model_evaluation import ModelEvaluationTrainingPipeline
from src.utils.logger import get_logger, log_spacer
from src.utils.exception import CustomException

logger = get_logger(__name__, headline="main.py")

if __name__ == "__main__":
    # Stage 01: Data Ingestion
    STAGE_NAME = "Data Ingestion stage"
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        data_ingestion = DataIngestionTrainingPipeline()
        data_ingestion.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e

    log_spacer()

    # Stage 02: Data Validation
    STAGE_NAME = "Data Validation stage"
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        data_validation = DataValidationTrainingPipeline()
        data_validation.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e

    log_spacer()

    # Stage 03: Data Transformation
    STAGE_NAME = "Data Transformation stage"
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        data_transformation = DataTransformationTrainingPipeline()
        data_transformation.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e
    log_spacer()

    # Stage 04: Model Trainer
    STAGE_NAME = "Model Trainer stage"
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        model_trainer = ModelTrainerTrainingPipeline()
        model_trainer.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e

    log_spacer()

    # Stage 05: Model Evaluation
    STAGE_NAME = "Model Evaluation stage"
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        model_evaluation = ModelEvaluationTrainingPipeline()
        model_evaluation.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e
