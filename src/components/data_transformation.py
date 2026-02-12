"""
Data Transformation Component.

This module handles the preprocessing of data for the model pipeline:
- Imputing missing values with 'median' (numeric) and 'constant' (categorical).
- Scaling features using RobustScaler (robust to outliers).
- Encoding categorical variables using OneHotEncoder.
- Saving the preprocessor object for consistent inference.
"""

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
import sys
from src.entity.config_entity import DataTransformationConfig
from src.utils.logger import get_logger
from src.utils.exception import CustomException

logger = get_logger(__name__)


class DataTransformation:
    """
    Handles the preprocessing of data for the model pipeline.
    """

    def __init__(self, config: DataTransformationConfig):
        self.config = config

    def get_data_transformer_object(self) -> ColumnTransformer:
        """
        Creates a ColumnTransformer pipeline for mixed feature types.

        Returns:
            ColumnTransformer: A sklearn column transformer.
        """

        num_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", RobustScaler()),
            ]
        )

        cat_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                (
                    "one_hot_encoder",
                    OneHotEncoder(sparse_output=False, handle_unknown="ignore"),
                ),
            ]
        )

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", num_pipeline, self.numerical_cols),
                ("cat", cat_pipeline, self.categorical_cols),
            ],
            remainder="drop",  # Drop the cols_to_drop and target (handled separately)
        )

        return preprocessor

    def initiate_data_transformation(self):
        """
        Executes the data transformation stage.
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

            # 2. Identify Columns
            target_col = "target"

            # Define columns to drop and categorical columns explicitly
            cols_to_drop = [
                "id_empresa",
                "ano",
                "default_probability",
            ]
            categorical_cols = []  # No categorical columns in current raw data

            # Set instance variables so they are available for get_data_transformer_object
            self.cols_to_drop = cols_to_drop
            self.categorical_cols = categorical_cols

            # Filter out target and drop columns to get input features
            all_cols = df_train.columns
            input_features = [
                c for c in all_cols if c not in [target_col] + self.cols_to_drop
            ]

            # Identify numerical cols dynamically: All input features that are NOT categorical
            numerical_cols = [c for c in input_features if c not in categorical_cols]

            # Set numerical cols instance variable
            self.numerical_cols = numerical_cols

            logger.info(f"Numerical cols: {numerical_cols}")
            logger.info(f"Categorical cols: {categorical_cols}")

            # 3. Fit Preprocessor on Train
            preprocessor = self.get_data_transformer_object()

            X_train = df_train[input_features]
            y_train = df_train[target_col]

            X_val = df_val[input_features]
            y_val = df_val[target_col]

            X_test = df_test[input_features]
            y_test = df_test[target_col]

            logger.info("Fitting preprocessor on training data...")
            # Fit on X_train
            preprocessor.fit(X_train)

            # 4. Transform All Splits
            X_train_transformed = preprocessor.transform(X_train)
            X_val_transformed = preprocessor.transform(X_val)
            X_test_transformed = preprocessor.transform(X_test)

            # 5. Save Preprocessor
            joblib.dump(preprocessor, self.config.preprocessor_path)
            logger.info(f"Saved preprocessor to {self.config.preprocessor_path}")

            # 6. Reconstruct DataFrames (Optional but good for debug/storage)
            # Get feature names from OHE
            try:
                cat_encoder = preprocessor.named_transformers_["cat"].named_steps[
                    "one_hot_encoder"
                ]
                cat_feature_names = cat_encoder.get_feature_names_out(categorical_cols)
            except AttributeError:
                # Fallback if specific step name changes or simplistic pipeline
                cat_feature_names = categorical_cols  # Should not happen with OHE

            final_columns = numerical_cols + list(cat_feature_names) + [target_col]

            # Helper to combine X and y
            def save_transformed(X_arr, y_series, path):
                # X_arr is numpy array (dense)
                df_trans = pd.DataFrame(X_arr, columns=final_columns[:-1])
                df_trans[target_col] = y_series.values
                df_trans.to_csv(path, index=False)
                return df_trans.shape

            # 7. Save Transformed Data
            train_shape = save_transformed(
                X_train_transformed, y_train, self.config.root_dir / "train.csv"
            )
            val_shape = save_transformed(
                X_val_transformed, y_val, self.config.root_dir / "val.csv"
            )
            test_shape = save_transformed(
                X_test_transformed, y_test, self.config.root_dir / "test.csv"
            )

            logger.info(
                f"Saved transformed datasets. Train: {train_shape}, Val: {val_shape}, Test: {test_shape}"
            )

        except Exception as e:
            raise CustomException(e, sys)
