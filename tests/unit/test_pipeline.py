"""
Unit tests for pipeline stages.
"""

from unittest.mock import patch

from src.pipeline.stage_01_data_ingestion import DataIngestionTrainingPipeline
from src.pipeline.stage_02_data_validation import DataValidationTrainingPipeline
from src.pipeline.stage_03_data_transformation import DataTransformationTrainingPipeline
from src.pipeline.stage_04_model_trainer import ModelTrainerTrainingPipeline
from src.pipeline.stage_05_model_evaluation import ModelEvaluationTrainingPipeline


def test_stage_01_data_ingestion():
    """Test data ingestion stage orchestration."""
    with (
        patch("src.pipeline.stage_01_data_ingestion.ConfigurationManager"),
        patch("src.pipeline.stage_01_data_ingestion.DataIngestion") as mock_comp,
    ):
        pipeline = DataIngestionTrainingPipeline()
        pipeline.main()

        mock_comp.return_value.initiate_data_ingestion.assert_called_once()


def test_stage_02_data_validation():
    """Test data validation stage orchestration."""
    with (
        patch("src.pipeline.stage_02_data_validation.ConfigurationManager"),
        patch("src.pipeline.stage_02_data_validation.DataValidation") as mock_comp,
    ):
        pipeline = DataValidationTrainingPipeline()
        pipeline.main()

        mock_comp.return_value.validate_all_columns.assert_called_once()


def test_stage_03_data_transformation():
    """Test data transformation stage orchestration."""
    with (
        patch("src.pipeline.stage_03_data_transformation.ConfigurationManager"),
        patch(
            "src.pipeline.stage_03_data_transformation.DataTransformation"
        ) as mock_comp,
    ):
        pipeline = DataTransformationTrainingPipeline()
        pipeline.main()

        mock_comp.return_value.initiate_data_transformation.assert_called_once()


def test_stage_04_model_trainer():
    """Test model trainer stage orchestration."""
    with (
        patch("src.pipeline.stage_04_model_trainer.ConfigurationManager"),
        patch("src.pipeline.stage_04_model_trainer.ModelTrainer") as mock_comp,
    ):
        pipeline = ModelTrainerTrainingPipeline()
        pipeline.main()

        mock_comp.return_value.train.assert_called_once()


def test_stage_05_model_evaluation():
    """Test model evaluation stage orchestration."""
    with (
        patch("src.pipeline.stage_05_model_evaluation.ConfigurationManager"),
        patch("src.pipeline.stage_05_model_evaluation.ModelEvaluation") as mock_comp,
    ):
        pipeline = ModelEvaluationTrainingPipeline()
        pipeline.main()

        mock_comp.return_value.log_into_mlflow.assert_called_once()
