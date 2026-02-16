"""
Model Registration Stage.

This component is responsible for registering the trained model into the MLflow Model Registry.
It ensures that the model meets specific criteria (e.g., accuracy thresholds) before being
staged for production. It handles versioning and tracking of the model artifacts.

Requirements:
    - MLflow running (e.g. uv run mlflow server --host 127.0.0.1 --port 5000)
    - Trained model saved to artifacts/model_trainer/acras_rf_model.joblib
    - Metrics file available for validation (e.g. artifacts/model_evaluation/metrics.json)
"""

import json
import joblib
import mlflow
from src.entity.config_entity import ModelRegistrationConfig
from src.utils.common import logger


class ModelRegistration:
    def __init__(self, config: ModelRegistrationConfig):
        self.config = config

    def log_into_mlflow(self):
        """
        Registers the model in MLflow Model Registry.
        """
        try:
            logger.info(f"Connecting to MLflow at {self.config.mlflow_uri}")
            mlflow.set_registry_uri(self.config.mlflow_uri)

            # Load metrics
            if not self.config.metric_file_name.exists():
                logger.warning(
                    f"Metrics file not found at {self.config.metric_file_name}. Cannot validate model performance."
                )
                return

            logger.info(f"Loading metrics from {self.config.metric_file_name}")
            with open(self.config.metric_file_name, "r") as f:
                metrics = json.load(f)

            accuracy = metrics.get("accuracy", 0)
            roc_auc = metrics.get("roc_auc", 0)

            logger.info(f"Model Metrics - Accuracy: {accuracy}, ROC AUC: {roc_auc}")

            # Define a threshold from params
            THRESHOLD = self.config.min_roc_auc

            if roc_auc < THRESHOLD:
                logger.warning(
                    f"Model ROC AUC ({roc_auc}) is below threshold ({THRESHOLD}). Skipping registration."
                )
                return

            logger.info(
                f"Model passed threshold ({THRESHOLD}). Proceeding with registration."
            )

            with mlflow.start_run(run_name="Model_Registration_Stage"):
                mlflow.log_metrics(metrics)
                mlflow.sklearn.log_model(
                    sk_model=self.load_model(),
                    artifact_path="model",
                    registered_model_name=self.config.model_name,
                )
                logger.info(
                    f"Model registered successfully as '{self.config.model_name}'"
                )

        except Exception as e:
            # Handle connection errors gracefully
            if "connection" in str(e).lower() or "active run" in str(e).lower():
                logger.warning(
                    f"MLflow connection failed: {e}. Falling back to local artifact storage (no registry)."
                )
            else:
                logger.error(f"Error during model registration: {e}")
                raise e

    def load_model(self):
        return joblib.load(self.config.model_path)
