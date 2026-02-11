"""
Configuration Manager for the MLOps Pipeline.

- This module serves as the 'Brain' of the system, responsible for coordinating configurations
and parameters across the pipeline.
- It centralizes the orchestration of configurations and parameters,
integrating with DVC for data versioning.
- It transforms raw YAML inputs into strictly-typed Configuration Entities,
providing a robust and reproducible interface for all downstream pipeline components.
"""

from src.constants import CONFIG_FILE_PATH, PARAMS_FILE_PATH
from src.utils.common import read_yaml, create_directories
from src.entity.config_entity import DataIngestionConfig
from pathlib import Path


class ConfigurationManager:
    def __init__(
        self, config_filepath=CONFIG_FILE_PATH, params_filepath=PARAMS_FILE_PATH
    ):
        self.config = read_yaml(config_filepath)
        self.params = read_yaml(params_filepath)

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
        )

        return data_ingestion_config
