"""
Main entry point for the Agentic Credit Risk Assessment System (ACRAS) pipeline.

This script allows for manual orchestration of the pipeline stages for debugging
and development purposes.

Usage:
    uv run python main.py
"""

import sys

from src.pipeline.stage_00_data_augmentation import DataAugmentationTrainingPipeline
from src.pipeline.stage_01_data_ingestion import DataIngestionTrainingPipeline
from src.pipeline.stage_02_data_validation import DataValidationTrainingPipeline
from src.pipeline.stage_03_data_transformation import DataTransformationTrainingPipeline
from src.pipeline.stage_04_model_trainer import ModelTrainerTrainingPipeline
from src.pipeline.stage_05_model_evaluation import ModelEvaluationTrainingPipeline
from src.pipeline.stage_06_model_registration import ModelRegistrationTrainingPipeline
from src.pipeline.stage_07_eval_dataset_validation import EvalDatasetValidationPipeline
from src.utils.exception import CustomException
from src.utils.logger import get_logger, log_spacer

logger = get_logger(__name__, headline="main.py")

if __name__ == "__main__":
    # Stage 00: Data Augmentation
    STAGE_NAME = "Data Augmentation stage"
    try:
        logger.info(f"STARTED: {STAGE_NAME}")
        data_augmentation = DataAugmentationTrainingPipeline()
        data_augmentation.main()
        logger.info(f"COMPLETED: {STAGE_NAME}")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e

    log_spacer()

    # Stage 01: Data Ingestion
    STAGE_NAME = "Data Ingestion stage"
    try:
        logger.info(f"STARTED: {STAGE_NAME}")
        data_ingestion = DataIngestionTrainingPipeline()
        data_ingestion.main()
        logger.info(f"COMPLETED: {STAGE_NAME}")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e

    log_spacer()

    # Stage 02: Data Validation
    STAGE_NAME = "Data Validation stage"
    try:
        logger.info(f"STARTED: {STAGE_NAME}")
        data_validation = DataValidationTrainingPipeline()
        data_validation.main()
        logger.info(f"COMPLETED: {STAGE_NAME}")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e

    log_spacer()

    # Stage 03: Data Transformation
    STAGE_NAME = "Data Transformation stage"
    try:
        logger.info(f"STARTED: {STAGE_NAME}")
        data_transformation = DataTransformationTrainingPipeline()
        data_transformation.main()
        logger.info(f"COMPLETED: {STAGE_NAME}")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e
    log_spacer()

    # Stage 04: Model Trainer
    STAGE_NAME = "Model Trainer stage"
    try:
        logger.info(f"STARTED: {STAGE_NAME}")
        model_trainer = ModelTrainerTrainingPipeline()
        model_trainer.main()
        logger.info(f"COMPLETED: {STAGE_NAME}")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e

    log_spacer()

    # Stage 05: Model Evaluation
    STAGE_NAME = "Model Evaluation stage"
    try:
        logger.info(f"STARTED: {STAGE_NAME}")
        model_evaluation = ModelEvaluationTrainingPipeline()
        model_evaluation.main()
        logger.info(f"COMPLETED: {STAGE_NAME}")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e

    log_spacer()

    # Stage 06: Model Registration
    STAGE_NAME = "Model Registration stage"
    try:
        from src.pipeline.stage_06_model_registration import (
            ModelRegistrationTrainingPipeline,
        )

        logger.info(f"STARTED: {STAGE_NAME}")
        model_registration = ModelRegistrationTrainingPipeline()
        model_registration.main()
        logger.info(f"COMPLETED: {STAGE_NAME}")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e

    log_spacer()

    # Stage 07: Evaluation Dataset Validation
    STAGE_NAME = "Evaluation Dataset Validation stage"
    try:
        logger.info(f"STARTED: {STAGE_NAME}")
        eval_dataset_validation = EvalDatasetValidationPipeline()
        eval_dataset_validation.main()
        logger.info(f"COMPLETED: {STAGE_NAME}")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e
