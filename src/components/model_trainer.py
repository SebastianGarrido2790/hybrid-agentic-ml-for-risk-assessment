"""
Model Training Component.

This module handles:
- Loading transformed data.
- Training a RandomForestClassifier (Baseline).
- Saving the trained model.
"""

import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
import sys
from src.entity.config_entity import ModelTrainerConfig
from src.utils.logger import get_logger
from src.utils.exception import CustomException

logger = get_logger(__name__)


class ModelTrainer:
    """
    Trains the machine learning model.
    """

    def __init__(self, config: ModelTrainerConfig):
        self.config = config

    def train(self):
        """
        Trains the model and saves it.
        """
        logger.info("Starting Model Training Stage")
        try:
            train_data = pd.read_csv(self.config.train_data_path)
            # val_data = pd.read_csv(self.config.val_data_path) # Validation done in next stage (Evaluation) or used for early stopping if supported

            # Prepare X and y
            target_col = "target"
            X_train = train_data.drop(columns=[target_col])
            y_train = train_data[target_col]

            logger.info(f"Training data shape: {X_train.shape}")

            # Initialize Model
            model = RandomForestClassifier(
                n_estimators=self.config.n_estimators,
                min_samples_leaf=self.config.min_samples_leaf,
                class_weight=self.config.class_weight,
                n_jobs=self.config.n_jobs,
                random_state=self.config.random_state,
            )

            # Train
            model.fit(X_train, y_train)
            logger.info("Model training completed")

            # Save Model
            joblib.dump(model, self.config.root_dir / self.config.model_name)
            logger.info(
                f"Model saved to {self.config.root_dir / self.config.model_name}"
            )

        except Exception as e:
            raise CustomException(e, sys)
