"""
Data Transformation Component.

This module handles the preprocessing of data for the model pipeline:
- Imputing missing values with 'median' (robust to outliers).
- Standardizing features (Z-score normalization) for model stability.
- Transforming features using a pipeline.
- Saving the preprocessor object for consistent inference.
"""

import joblib
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from src.entity.config_entity import DataTransformationConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataTransformation:
    """
    Handles the preprocessing of data for the model pipeline.
    Strategy:
    - Impute missing values with 'median' (robust to outliers).
    - Standardize features (Z-score normalization) for model stability.
    - Save the preprocessor object for consistent inference.
    """

    def __init__(self, config: DataTransformationConfig):
        self.config = config

    def get_data_transformer_object(self) -> Pipeline:
        """
        Creates a pipeline for numerical feature transformation.

        Returns:
            Pipeline: A sklearn pipeline with Imputer and Scaler.
        """
        pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        return pipeline

    def initiate_data_transformation(self):
        """
        Executes the data transformation stage:
        1. Loads Train/Val/Test data.
        2. Fits the preprocessor on the Training set (preventing data leakage).
        3. Transforms all sets.
        4. Saves the preprocessor and transformed datasets.
        """
        logger.info("Starting Data Transformation Stage")

        try:
            # 1. Load Data
            train_path = self.config.data_path / "train.csv"
            val_path = self.config.data_path / "val.csv"
            test_path = self.config.data_path / "test.csv"

            df_train = pd.read_csv(train_path)
            df_val = pd.read_csv(val_path)
            df_test = pd.read_csv(test_path)

            logger.info(f"Loaded datasets. Train shape: {df_train.shape}")

            # 2. Select Features to Transform
            # Exclude ID, Target, and any other metadata/targets
            # We want to transform only the INPUT features for the model
            exclude_cols = ["id_empresa", "target", "default_probability"]
            numerical_cols = [
                col
                for col in df_train.select_dtypes(include=[np.number]).columns
                if col not in exclude_cols
            ]

            logger.info(f"Features to transform: {numerical_cols}")

            # 3. Fit Preprocessor on Train
            preprocessor = self.get_data_transformer_object()

            # Fit only on the selected numerical columns of the training set
            preprocessor.fit(df_train[numerical_cols])

            # 4. Transform All Splits
            def transform_dataframe(df, cols, pipeline):
                df_transformed = df.copy()
                transformed_data = pipeline.transform(df[cols])
                # Update the columns with transformed values
                df_transformed[cols] = transformed_data
                return df_transformed

            train_transformed = transform_dataframe(
                df_train, numerical_cols, preprocessor
            )
            val_transformed = transform_dataframe(df_val, numerical_cols, preprocessor)
            test_transformed = transform_dataframe(
                df_test, numerical_cols, preprocessor
            )

            # 5. Save Preprocessor
            joblib.dump(preprocessor, self.config.preprocessor_path)
            logger.info(f"Saved preprocessor to {self.config.preprocessor_path}")

            # 6. Save Transformed Data
            train_save_path = self.config.root_dir / "train.csv"
            val_save_path = self.config.root_dir / "val.csv"
            test_save_path = self.config.root_dir / "test.csv"

            train_transformed.to_csv(train_save_path, index=False)
            val_transformed.to_csv(val_save_path, index=False)
            test_transformed.to_csv(test_save_path, index=False)

            logger.info(
                f"Saved transformed datasets to {self.config.root_dir}. Train shape: {train_transformed.shape}"
            )

        except Exception as e:
            logger.error(f"Error in data transformation: {e}")
            raise e
