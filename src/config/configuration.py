"""
Configuration Manager for the MLOps Pipeline.

- This module serves as the 'Brain' of the system, responsible for coordinating configurations
and parameters across the pipeline.
- It centralizes the orchestration of configurations and parameters,
integrating with DVC for data versioning.
- It transforms raw YAML inputs into strictly-typed Configuration Entities,
providing a robust and reproducible interface for all downstream pipeline components.
"""

from src.constants import CONFIG_FILE_PATH, PARAMS_FILE_PATH, SCHEMA_FILE_PATH
from src.utils.common import read_yaml, create_directories
from src.entity.config_entity import (
    DataIngestionConfig,
    DataValidationConfig,
    DataTransformationConfig,
    ModelTrainerConfig,
    ModelEvaluationConfig,
)
from pathlib import Path
from src.utils.mlflow_config import get_mlflow_uri


class ConfigurationManager:
    def __init__(
        self,
        config_filepath=CONFIG_FILE_PATH,
        params_filepath=PARAMS_FILE_PATH,
        schema_filepath=SCHEMA_FILE_PATH,
    ):
        self.config = read_yaml(config_filepath)
        self.params = read_yaml(params_filepath)
        self.schema = read_yaml(schema_filepath)

        create_directories([self.config.artifacts_root])

    def get_data_ingestion_config(self) -> DataIngestionConfig:
        config = self.config.data_ingestion
        params = self.params.data_split

        create_directories([config.root_dir])

        data_ingestion_config = DataIngestionConfig(
            root_dir=Path(config.root_dir),
            source_data_dir=Path(config.source_data_dir),
            financial_data_file=config.financial_data_file,
            pd_data_file=config.pd_data_file,
            unzip_dir=Path(config.unzip_dir),
            test_size=params.test_size,
            val_size=params.val_size,
            random_state=params.random_state,
            target_column=self.schema.target_column,
        )

        return data_ingestion_config

    def get_data_validation_config(self) -> DataValidationConfig:
        config = self.config.data_validation
        schema = self.schema.columns

        create_directories([config.root_dir])

        data_validation_config = DataValidationConfig(
            root_dir=Path(config.root_dir),
            STATUS_FILE=config.STATUS_FILE,
            unzip_data_dir=Path(config.unzip_data_dir),
            all_schema=schema,
        )

        return data_validation_config

    def get_data_transformation_config(self) -> DataTransformationConfig:
        config = self.config.data_transformation

        create_directories([config.root_dir])

        data_transformation_config = DataTransformationConfig(
            root_dir=Path(config.root_dir),
            data_path=Path(config.data_path),
            preprocessor_path=Path(config.preprocessor_path),
        )

        return data_transformation_config

    def get_model_trainer_config(self) -> ModelTrainerConfig:
        config = self.config.model_trainer
        params = self.params.model_params

        create_directories([config.root_dir])

        model_trainer_config = ModelTrainerConfig(
            root_dir=Path(config.root_dir),
            train_data_path=Path(config.train_data_path),
            val_data_path=Path(config.val_data_path),
            model_name=config.model_name,
            n_estimators=params.n_estimators,
            min_samples_leaf=params.min_samples_leaf,
            class_weight=params.class_weight,
            n_jobs=params.n_jobs,
            random_state=self.params.data_split.random_state,
        )

        return model_trainer_config

    def get_model_evaluation_config(self) -> ModelEvaluationConfig:
        config = self.config.model_evaluation
        params = self.params.model_params
        target_column = self.schema.target_column

        create_directories([config.root_dir])

        model_evaluation_config = ModelEvaluationConfig(
            root_dir=Path(config.root_dir),
            test_data_path=Path(config.test_data_path),
            model_path=Path(config.model_path),
            all_params=params,
            metric_file_name=Path(config.metric_file_name),
            target_column=target_column,
            mlflow_uri=get_mlflow_uri(),
            experiment_name=config.experiment_name,
            registered_model_name=config.registered_model_name,
            mlflow_model_name=config.mlflow_model_name,
        )

        return model_evaluation_config
