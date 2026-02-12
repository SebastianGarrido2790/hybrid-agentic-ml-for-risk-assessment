"""
Utility module for defining and managing file paths used throughout the project.
Includes automatic environment detection from `.env`.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# --- Load environment variables (once, globally) ---
load_dotenv()
ENV = os.getenv("ENV", "local").lower()  # e.g., "local", "staging", "production"

# --- Project Root ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# --- Artifacts (MLOps Pipeline Outputs) ---
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
DATA_INGESTION_DIR = ARTIFACTS_DIR / "data_ingestion"
DATA_VALIDATION_DIR = ARTIFACTS_DIR / "data_validation"
DATA_TRANSFORMATION_DIR = ARTIFACTS_DIR / "data_transformation"
MODEL_TRAINER_DIR = ARTIFACTS_DIR / "model_trainer"
MODEL_EVALUATION_DIR = ARTIFACTS_DIR / "model_evaluation"

# Transformed data paths
TRAIN_PATH = DATA_TRANSFORMATION_DIR / "train.csv"
TEST_PATH = DATA_TRANSFORMATION_DIR / "test.csv"
VAL_PATH = DATA_TRANSFORMATION_DIR / "val.csv"

# Trained model path
MODEL_PATH = MODEL_TRAINER_DIR / "acras_rf_model.joblib"

# --- Traditional Raw Data (Inputs) ---
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

# --- Logs ---
LOGS_DIR = PROJECT_ROOT / "logs"
MLRUNS_DIR = PROJECT_ROOT / "mlruns"

# --- Ensure core directories exist ---
for path in [
    ARTIFACTS_DIR,
    DATA_DIR,
    RAW_DATA_DIR,
    LOGS_DIR,
    MLRUNS_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)
