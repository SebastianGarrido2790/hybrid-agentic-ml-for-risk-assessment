"""
Centralized storage for constant file paths used throughout the project.
This ensures consistency across different modules when accessing configuration and parameter files.
"""

from pathlib import Path

CONFIG_FILE_PATH = Path("config/config.yaml")
PARAMS_FILE_PATH = Path("params.yaml")
