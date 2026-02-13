"""
Model Evaluation Component.

This module handles:
- Loading the trained model and test dataset.
- Calculating performance metrics (Accuracy, Precision, Recall, F1, ROC-AUC).
- Generating and saving evaluation plots.
- Logging metrics, parameters, and models to MLflow.
"""

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from urllib.parse import urlparse
import mlflow
import mlflow.sklearn
import joblib
from src.entity.config_entity import ModelEvaluationConfig
from src.utils.common import save_json, create_directories
from pathlib import Path
from src.utils.exception import CustomException
from src.utils.logger import get_logger
import sys

logger = get_logger(__name__)


class ModelEvaluation:
    """
    Evaluates the performance of a trained model and logs results.
    """

    def __init__(self, config: ModelEvaluationConfig):
        """
        Initializes the ModelEvaluation component with configuration.

        Args:
            config (ModelEvaluationConfig): Configuration entity for model evaluation.
        """
        self.config = config

    def eval_metrics(self, actual, pred):
        """
        Calculates core classification metrics.

        Args:
            actual (array-like): Ground truth (correct) target values.
            pred (array-like): Estimated targets as returned by a classifier.

        Returns:
            tuple: (accuracy, precision, recall, f1)
        """
        accuracy = accuracy_score(actual, pred)
        precision = precision_score(actual, pred, zero_division=0)
        recall = recall_score(actual, pred, zero_division=0)
        f1 = f1_score(actual, pred, zero_division=0)
        return accuracy, precision, recall, f1

    def save_roc_plot(self, actual, prob, plot_path):
        """
        Generates and saves the Receiver Operating Characteristic (ROC) curve.

        Args:
            actual (array-like): Ground truth (correct) target values.
            prob (array-like): Predicted probabilities for the positive class.
            plot_path (Path): File path where the plot will be saved.
        """
        import matplotlib.pyplot as plt
        from sklearn.metrics import roc_curve, auc
        import seaborn as sns

        try:
            sns.set_theme(style="whitegrid")
            plt.figure(figsize=(10, 8))

            # Handle cases where ROC-AUC might not be calculable (e.g., only one class in test set)
            if len(actual.unique()) > 1:
                fpr, tpr, _ = roc_curve(actual, prob)
                roc_auc = auc(fpr, tpr)
                plt.plot(
                    fpr,
                    tpr,
                    color="darkorange",
                    lw=2,
                    label=f"ROC curve (area = {roc_auc:0.2f})",
                )
            else:
                plt.text(
                    0.5,
                    0.5,
                    "ROC-AUC not calculable\n(Only one class in test data)",
                    horizontalalignment="center",
                    verticalalignment="center",
                    fontsize=14,
                )
                roc_auc = 0.0

            plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel("False Positive Rate", fontsize=12)
            plt.ylabel("True Positive Rate", fontsize=12)
            plt.title("Receiver Operating Characteristic (ROC)", fontsize=15)
            plt.legend(loc="lower right", fontsize=12)

            plt.tight_layout()
            plt.savefig(plot_path)
            plt.close()
            logger.info(f"ROC plot saved to {plot_path}")
        except Exception as e:
            logger.warning(f"Failed to create ROC plot: {e}")

    def log_into_mlflow(self):
        """
        Main execution logic for the evaluation stage.
        Loads data, calculates metrics, saves them locally, and logs to MLflow.

        Raises:
            CustomException: If any error occurs during the evaluation process.
        """
        try:
            test_data = pd.read_csv(self.config.test_data_path)
            model = joblib.load(self.config.model_path)

            test_x = test_data.drop([self.config.target_column], axis=1)
            test_y = test_data[[self.config.target_column]]

            # Only set registry URI if it is a valid remote URI
            mlflow_uri = self.config.mlflow_uri
            if mlflow_uri and mlflow_uri.strip() and not mlflow_uri.startswith("file:"):
                mlflow.set_registry_uri(mlflow_uri)
                mlflow.set_tracking_uri(mlflow_uri)
            else:
                mlflow.set_tracking_uri("file:./mlruns")

            # Experiment Setup
            try:
                mlflow.set_experiment(self.config.experiment_name)
            except Exception as e:
                logger.warning(
                    f"Failed to set experiment on remote server: {e}. Falling back to local './mlruns'."
                )
                mlflow.set_registry_uri(None)
                mlflow.set_tracking_uri("file:./mlruns")
                mlflow.set_experiment(self.config.experiment_name)

            tracking_uri = mlflow.get_tracking_uri()
            tracking_url_type_store = urlparse(tracking_uri).scheme
            logger.info(f"MLflow Tracking URI: {tracking_uri}")

            # Calculate metrics first (Critical for DVC)
            predicted_qualities = model.predict(test_x)

            y_prob = None
            if hasattr(model, "predict_proba"):
                y_prob = model.predict_proba(test_x)[:, 1]
                # Check for single-class data to avoid ROC-AUC failure
                if len(test_y[self.config.target_column].unique()) > 1:
                    try:
                        roc_auc = roc_auc_score(test_y, y_prob)
                    except Exception as e:
                        logger.warning(f"ROC-AUC calculation failed: {e}")
                        roc_auc = 0.5
                else:
                    logger.warning(
                        "ROC-AUC score could not be calculated (only one class present in test data). Returning 0.5"
                    )
                    roc_auc = 0.5
            else:
                roc_auc = 0.5

            # Ensure roc_auc is a valid number for JSON
            if pd.isna(roc_auc):
                roc_auc = 0.5

            (accuracy, precision, recall, f1) = self.eval_metrics(
                test_y, predicted_qualities
            )

            scores = {
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "roc_auc": float(roc_auc),
            }
            save_json(path=Path(self.config.metric_file_name), data=scores)

            # Define plot path
            plot_dir = Path(self.config.root_dir)
            create_directories([plot_dir])
            roc_plot_path = plot_dir / "roc_auc_curve.png"

            if y_prob is not None:
                self.save_roc_plot(
                    test_y[self.config.target_column], y_prob, roc_plot_path
                )

            # Optional MLflow logging (Fault Tolerant)
            try:
                run_name = f"RF_Eval_{pd.Timestamp.now().strftime('%Y_%m_%d_%H_%M')}"
                with mlflow.start_run(run_name=run_name):
                    mlflow.log_params(self.config.all_params)
                    mlflow.log_metrics(scores)

                    if roc_plot_path.exists():
                        mlflow.log_artifact(str(roc_plot_path), "plots")

                    if tracking_url_type_store != "file":
                        mlflow.sklearn.log_model(
                            model,
                            self.config.mlflow_model_name,
                            registered_model_name=self.config.registered_model_name,
                        )
                    else:
                        mlflow.sklearn.log_model(model, self.config.mlflow_model_name)
            except Exception as e:
                logger.warning(f"MLflow logging failed but pipeline continues: {e}")

        except Exception as e:
            raise CustomException(e, sys)
