"""
Configuration entities for the Agentic Credit Risk Assessment System (ACRAS).

This module defines a two-tier configuration structure:
1. Pydantic BaseModels: Used for strict YAML parsing and schema validation at boundaries.
2. Dataclass Entities: Used as strictly-typed, immutable objects for internal pipeline logic.

Enforcing strict typing and strict schema validation for all configurations.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict


@dataclass(frozen=True)
class RiskParamsConfig:
    low_threshold: float
    high_threshold: float
    mora_critical: float
    current_ratio_critical: float


@dataclass(frozen=True)
class FeatureParamsConfig:
    insolvent_cap: float


@dataclass(frozen=True)
class DataAugmentationConfig:
    root_dir: Path
    raw_data_dir: Path
    processed_data_dir: Path
    n_samples: int


@dataclass(frozen=True)
class DataIngestionConfig:
    root_dir: Path
    source_data_dir: Path
    financial_data_file: str
    pd_data_file: str
    unzip_dir: Path
    test_size: float
    val_size: float
    random_state: int
    target_column: str
    insolvent_cap: float


@dataclass(frozen=True)
class DataValidationConfig:
    root_dir: Path
    STATUS_FILE: str
    unzip_data_dir: Path
    all_schema: dict[str, str]


@dataclass(frozen=True)
class DataTransformationConfig:
    root_dir: Path
    data_path: Path
    preprocessor_path: Path
    cols_to_drop: list[str]
    target_column: str


@dataclass(frozen=True)
class ModelTrainerConfig:
    root_dir: Path
    train_data_path: Path
    val_data_path: Path
    model_name: str
    n_estimators: int
    min_samples_leaf: int
    class_weight: str
    n_jobs: int
    random_state: int
    target_column: str


@dataclass(frozen=True)
class ModelEvaluationConfig:
    root_dir: Path
    test_data_path: Path
    model_path: Path
    all_params: dict[str, Any]
    metric_file_name: Path
    target_column: str
    mlflow_uri: str
    experiment_name: str
    registered_model_name: str
    mlflow_model_name: str


@dataclass(frozen=True)
class ModelRegistrationConfig:
    root_dir: Path
    model_path: Path
    metric_file_name: Path
    model_name: str
    mlflow_uri: str
    min_roc_auc: float


# --- YAML Structure Models (Typed Boundaries) ---


class DataIngestionYamlConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    root_dir: str
    source_data_dir: str
    financial_data_file: str
    pd_data_file: str
    unzip_dir: str


class DataAugmentationYamlConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    root_dir: str
    raw_data_dir: str
    processed_data_dir: str


class DataValidationYamlConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    root_dir: str
    unzip_data_dir: str
    STATUS_FILE: str


class DataTransformationYamlConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    root_dir: str
    data_path: str
    preprocessor_path: str
    cols_to_drop: list[str]


class ModelTrainerYamlConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    root_dir: str
    train_data_path: str
    val_data_path: str
    model_name: str


class ModelEvaluationYamlConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    root_dir: str
    test_data_path: str
    model_path: str
    metric_file_name: str
    experiment_name: str
    registered_model_name: str
    mlflow_model_name: str


class ModelRegistrationYamlConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    root_dir: str
    model_path: str
    metric_file_name: str
    model_name: str


class MasterConfig(BaseModel):
    """Schema for config/config.yaml"""

    model_config = ConfigDict(extra="forbid")
    artifacts_root: str
    data_ingestion: DataIngestionYamlConfig
    data_augmentation: DataAugmentationYamlConfig
    data_validation: DataValidationYamlConfig
    data_transformation: DataTransformationYamlConfig
    model_trainer: ModelTrainerYamlConfig
    model_evaluation: ModelEvaluationYamlConfig
    model_registration: ModelRegistrationYamlConfig


class DataSplitParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    test_size: float
    val_size: float
    random_state: int


class ModelParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    n_estimators: int
    min_samples_leaf: int
    class_weight: str
    n_jobs: int


class MLflowParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    uri: str


class RegistrationParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    min_roc_auc: float


class AugmentationParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    n_samples: int


class RiskThresholdsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    low: float
    high: float
    mora_critical: float
    current_ratio_critical: float


class FeatureParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    insolvent_cap: float


class MasterParams(BaseModel):
    """Schema for config/params.yaml"""

    model_config = ConfigDict(extra="forbid")
    data_split: DataSplitParams
    model_params: ModelParams
    mlflow: MLflowParams
    registration_params: RegistrationParams
    augmentation: AugmentationParams
    risk_thresholds: RiskThresholdsParams
    feature_params: FeatureParams


class MasterSchema(BaseModel):
    """Schema for config/schema.yaml"""

    model_config = ConfigDict(extra="forbid")
    columns: dict[str, str]
    target_column: str
