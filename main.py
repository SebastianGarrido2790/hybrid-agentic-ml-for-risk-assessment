"""
Main entry point for the Agentic Credit Risk Assessment System (ACRAS) pipeline.

This script allows for manual orchestration of the pipeline stages for debugging
and development purposes.

Usage:
    uv run python main.py
"""

from src.pipeline.stage_01_data_ingestion import DataIngestionTrainingPipeline
from src.pipeline.stage_02_data_transformation import DataTransformationTrainingPipeline
from src.utils.logger import get_logger, log_spacer

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
        logger.exception(e)
        raise e

    log_spacer()

    # Stage 02: Data Transformation
    STAGE_NAME = "Data Transformation stage"
    try:
        logger.info(f"🚀 {STAGE_NAME} started 🚀")
        data_transformation = DataTransformationTrainingPipeline()
        data_transformation.main()
        logger.info(f"✅ {STAGE_NAME} completed ✅")
    except Exception as e:
        logger.exception(e)
        raise e
    log_spacer()
