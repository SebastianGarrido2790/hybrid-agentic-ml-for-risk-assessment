"""
Common utility functions for the ACRAS MLOps pipeline.

This module provides deterministic helper functions for recurring tasks such as
safe YAML reading and directory management. Following Typed Boundaries convention,
it returns standard Python types (dict) to be validated by the configuration layer.
"""

import json
import os
from pathlib import Path
from typing import Any

import yaml

from src.utils.logger import get_logger

logger = get_logger(__name__)


def read_yaml(path_to_yaml: Path | str) -> dict[str, Any]:
    """Reads a YAML file and returns its content as a dictionary.

    Args:
        path_to_yaml (Path): Path to the YAML file.

    Returns:
        dict: Dictionary containing the YAML data.

    Raises:
        ValueError: If the YAML file is empty.
        Exception: For any other unexpected errors during file reading.
    """
    try:
        with open(path_to_yaml) as yaml_file:
            content = yaml.safe_load(yaml_file)
            if content is None:
                raise ValueError("yaml file is empty")
            logger.info(f"yaml file: {path_to_yaml} loaded successfully")
            return content
    except Exception as e:
        raise e


def create_directories(
    path_to_directories: list[Path | str], verbose: bool = True
) -> None:
    """Creates a list of directories if they do not already exist.

    Args:
        path_to_directories (list): List of paths to create.
        verbose (bool, optional): Whether to log the creation of each directory. Defaults to True.
    """
    for path in path_to_directories:
        os.makedirs(path, exist_ok=True)
        if verbose:
            logger.info(f"created directory at: {path}")


def save_json(path: Path, data: dict[str, Any]) -> None:
    """save json data

    Args:
        path (Path): path to json file
        data (dict): data to be saved in json file
    """
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    logger.info(f"json file saved at: {path}")
