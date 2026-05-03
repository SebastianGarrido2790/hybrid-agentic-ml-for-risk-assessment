"""
Centralized storage for constant file paths used throughout the project.
This ensures consistency across different modules when accessing configuration and parameter files.
"""

from pathlib import Path

CONFIG_FILE_PATH = Path("config/config.yaml")
PARAMS_FILE_PATH = Path("config/params.yaml")
SCHEMA_FILE_PATH = Path("config/schema.yaml")
# Automatically finds the top-level directory (the one containing 'src/')
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# --- Ensure directories exist ---
directories_to_create = [PROJECT_ROOT / "logs", PROJECT_ROOT / "artifacts"]

for path in directories_to_create:
    path.mkdir(parents=True, exist_ok=True)
