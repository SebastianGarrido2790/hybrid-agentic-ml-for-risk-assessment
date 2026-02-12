"""
Common utility functions for the MLOps pipeline.

This module contains helper functions for recurring tasks such as reading YAML files
and creating directories, ensuring a dry (Don't Repeat Yourself) architecture.
"""

import os
import yaml
from box import ConfigBox
from box.exceptions import BoxValueError
from pathlib import Path
from ensure import ensure_annotations
from src.utils.logger import get_logger
import json

logger = get_logger(__name__)


@ensure_annotations
def read_yaml(path_to_yaml: Path) -> ConfigBox:
    """Reads a YAML file and returns its content as a ConfigBox.

    ConfigBox allows accessing dictionary keys as attributes (e.g., config.key).

    Args:
        path_to_yaml (Path): Path to the YAML file.

    Returns:
        ConfigBox: ConfigBox containing the YAML data.

    Raises:
        ValueError: If the YAML file is empty.
        Exception: For any other unexpected errors during file reading.
    """
    try:
        with open(path_to_yaml) as yaml_file:
            content = yaml.safe_load(yaml_file)
            logger.info(f"yaml file: {path_to_yaml} loaded successfully")
            return ConfigBox(content)
    except BoxValueError:
        raise ValueError("yaml file is empty")
    except Exception as e:
        raise e


@ensure_annotations
def create_directories(path_to_directories: list, verbose: bool = True):
    """Creates a list of directories if they do not already exist.

    Args:
        path_to_directories (list): List of paths to create.
        verbose (bool, optional): Whether to log the creation of each directory. Defaults to True.
    """
    for path in path_to_directories:
        os.makedirs(path, exist_ok=True)
        if verbose:
            logger.info(f"created directory at: {path}")


@ensure_annotations
def save_json(path: Path, data: dict):
    """save json data

    Args:
        path (Path): path to json file
        data (dict): data to be saved in json file
    """
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    logger.info(f"json file saved at: {path}")
