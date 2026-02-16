"""
Configuration entities for the Agentic Credit Risk Assessment System (ACRAS).

This module defines dataclass entities to enforce strict type safety
and immutability to prevent attribute errors across different stages of the system.
"""

from dataclasses import dataclass
from pathlib import Path


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


@dataclass(frozen=True)
class DataValidationConfig:
    root_dir: Path
    STATUS_FILE: str
    unzip_data_dir: Path
    all_schema: dict


@dataclass(frozen=True)
class DataTransformationConfig:
    root_dir: Path
    data_path: Path
    preprocessor_path: Path


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


@dataclass(frozen=True)
class ModelEvaluationConfig:
    root_dir: Path
    test_data_path: Path
    model_path: Path
    all_params: dict
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
