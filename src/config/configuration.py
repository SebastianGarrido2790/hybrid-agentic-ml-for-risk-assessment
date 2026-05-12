"""
Configuration Manager for the ACRAS Agentic System.

Following Typed Configuration design pattern, this module orchestrates the system's
configuration bridge. It performs a three-stage validation process:
1. Raw I/O: Reads YAML files as standard dictionaries.
2. Structural Validation: Parses dictionaries into Pydantic models (MasterConfig/MasterParams).
3. Entity Mapping: Transforms validated models into immutable Dataclass entities for the pipeline.

This ensures that any configuration error is caught at startup with a descriptive ValidationError.
"""

from pathlib import Path

from src.constants import CONFIG_FILE_PATH, PARAMS_FILE_PATH, SCHEMA_FILE_PATH
from src.entity.config_entity import (
    DataAugmentationConfig,
    DataIngestionConfig,
    DataTransformationConfig,
    DataValidationConfig,
    FeatureParamsConfig,
    MasterConfig,
    MasterParams,
    MasterSchema,
    ModelEvaluationConfig,
    ModelRegistrationConfig,
    ModelTrainerConfig,
    RiskParamsConfig,
)
from src.utils.common import create_directories, read_yaml
from src.utils.mlflow_config import get_mlflow_uri


class ConfigurationManager:
    def __init__(
        self,
        config_filepath: str | Path = CONFIG_FILE_PATH,
        params_filepath: str | Path = PARAMS_FILE_PATH,
        schema_filepath: str | Path = SCHEMA_FILE_PATH,
    ):
        config_dict = read_yaml(config_filepath)
        params_dict = read_yaml(params_filepath)
        schema_dict = read_yaml(schema_filepath)

        self.config = MasterConfig(**config_dict)
        self.params = MasterParams(**params_dict)
        self.schema = MasterSchema(**schema_dict)

        create_directories([self.config.artifacts_root])

    def get_data_augmentation_config(self) -> DataAugmentationConfig:
        config = self.config.data_augmentation
        params = self.params.augmentation

        create_directories([config.root_dir])

        data_augmentation_config = DataAugmentationConfig(
            root_dir=Path(config.root_dir),
            raw_data_dir=Path(config.raw_data_dir),
            processed_data_dir=Path(config.processed_data_dir),
            n_samples=params.n_samples,
        )

        return data_augmentation_config

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
            insolvent_cap=self.params.feature_params.insolvent_cap,
        )

        return data_ingestion_config

    def get_data_validation_config(self) -> DataValidationConfig:
        config = self.config.data_validation
        schema = self.schema.columns

        create_directories([config.root_dir])

        data_validation_config = DataValidationConfig(
            root_dir=Path(config.root_dir),
            STATUS_FILE=config.STATUS_FILE,
            EXPECTATIONS_FILE=Path(config.EXPECTATIONS_FILE),
            unzip_data_dir=Path(config.unzip_data_dir),
            all_schema=schema,
        )

        return data_validation_config

    def get_data_transformation_config(self) -> DataTransformationConfig:
        config = self.config.data_transformation
        target_column = self.schema.target_column

        create_directories([config.root_dir])

        data_transformation_config = DataTransformationConfig(
            root_dir=Path(config.root_dir),
            data_path=Path(config.data_path),
            preprocessor_path=Path(config.preprocessor_path),
            cols_to_drop=config.cols_to_drop,
            target_column=target_column,
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
            target_column=self.schema.target_column,
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
            all_params=params.model_dump(),
            metric_file_name=Path(config.metric_file_name),
            target_column=target_column,
            mlflow_uri=get_mlflow_uri(),
            experiment_name=config.experiment_name,
            registered_model_name=config.registered_model_name,
            mlflow_model_name=config.mlflow_model_name,
        )

        return model_evaluation_config

    def get_model_registration_config(self) -> ModelRegistrationConfig:
        config = self.config.model_registration
        params = self.params.registration_params

        create_directories([config.root_dir])

        model_registration_config = ModelRegistrationConfig(
            root_dir=Path(config.root_dir),
            model_path=Path(config.model_path),
            metric_file_name=Path(config.metric_file_name),
            model_name=config.model_name,
            mlflow_uri=get_mlflow_uri(),
            min_roc_auc=params.min_roc_auc,
        )

        return model_registration_config

    def get_risk_params_config(self) -> RiskParamsConfig:
        params = self.params.risk_thresholds
        return RiskParamsConfig(
            low_threshold=params.low,
            high_threshold=params.high,
            mora_critical=params.mora_critical,
            current_ratio_critical=params.current_ratio_critical,
        )

    def get_feature_params_config(self) -> FeatureParamsConfig:
        params = self.params.feature_params
        return FeatureParamsConfig(
            insolvent_cap=params.insolvent_cap,
        )
