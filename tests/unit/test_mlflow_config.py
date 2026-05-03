"""
Unit tests for MLflow configuration utilities.

This module verifies the URI resolution logic, ensuring that environment variables,
staging defaults, and YAML fallbacks are correctly prioritized across different
environments (local, staging, production).
"""
import os
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
import yaml

from src.utils.mlflow_config import get_mlflow_uri


def test_get_mlflow_uri_env_var():
    """Test that MLFLOW_TRACKING_URI environment variable takes priority."""
    with patch.dict(os.environ, {"MLFLOW_TRACKING_URI": "http://env-uri:5000"}):
        uri = get_mlflow_uri()
        assert uri == "http://env-uri:5000"


def test_get_mlflow_uri_production_error():
    """Test that production mode raises RuntimeError if URI is missing."""
    with patch("src.utils.mlflow_config.ENV", "production"):
        with patch.dict(os.environ, {"MLFLOW_TRACKING_URI": ""}):
            if "MLFLOW_TRACKING_URI" in os.environ:
                del os.environ["MLFLOW_TRACKING_URI"]

            with pytest.raises(
                RuntimeError, match="Production mode requires MLFLOW_TRACKING_URI"
            ):
                get_mlflow_uri()


def test_get_mlflow_uri_staging_default():
    """Test that staging mode returns its default URI."""
    with patch("src.utils.mlflow_config.ENV", "staging"):
        with patch.dict(os.environ, {"MLFLOW_TRACKING_URI": ""}):
            if "MLFLOW_TRACKING_URI" in os.environ:
                del os.environ["MLFLOW_TRACKING_URI"]
            uri = get_mlflow_uri()
            assert uri == "http://staging-mlflow-server:5000"


def test_get_mlflow_uri_yaml_fallback():
    """Test that local mode falls back to params.yaml if env vars are missing."""
    mock_params = {"mlflow": {"uri": "http://yaml-uri:5000"}}
    yaml_content = yaml.dump(mock_params)

    with patch("src.utils.mlflow_config.ENV", "local"):
        with patch.dict(os.environ, {"MLFLOW_TRACKING_URI": ""}):
            if "MLFLOW_TRACKING_URI" in os.environ:
                del os.environ["MLFLOW_TRACKING_URI"]

            with patch("pathlib.Path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=yaml_content)):
                    uri = get_mlflow_uri()
                    assert uri == "http://yaml-uri:5000"


def test_get_mlflow_uri_final_fallback():
    """Test the ultimate fallback for local development."""
    with patch("src.utils.mlflow_config.ENV", "local"):
        with patch.dict(os.environ, {"MLFLOW_TRACKING_URI": ""}):
            if "MLFLOW_TRACKING_URI" in os.environ:
                del os.environ["MLFLOW_TRACKING_URI"]

            with patch("pathlib.Path.exists", return_value=False):
                uri = get_mlflow_uri()
                assert uri == "http://127.0.0.1:5000"
