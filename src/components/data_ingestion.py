"""
Data Ingestion Component.

This module handles the initial stage of the MLOps pipeline:
- Obtaining raw data from source files (Raw Data Integration).
- Merging Financial Statements and PD tables.
- Calculating Financial Ratios (Feature Engineering).
- Splitting the data into Train, Validation, and Test sets.
- Storing the splits as artifacts for downstream stages.
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import sys
from src.entity.config_entity import DataIngestionConfig
from src.config.configuration import ConfigurationManager
from src.utils.logger import get_logger
from src.utils.exception import CustomException
from src.features.build_features import engineer_features


logger = get_logger(__name__)


class DataIngestion:
    """
    Handles the ingestion, merging, feature engineering, and splitting of data for the ACRAS system.
    """

    def __init__(self, config: DataIngestionConfig):
        """
        Initializes the DataIngestion component with the provided configuration.

        Args:
            config (DataIngestionConfig): The configuration entity containing paths and split ratios.
        """
        self.config = config

    def _load_and_merge_raw_data(
        self, financial_path: str, pd_path: str
    ) -> pd.DataFrame:
        """
        Loads and merges Financial Statements and PD tables using aggregation to avoiding Cartesian products.
        Strategy:
        - Financials: Take the LATEST year per company.
        - PD: Take the MEAN of numerical columns per company (smoothed risk).
        """
        logger.info(f"Loading raw data from: {financial_path} and {pd_path}")

        if not os.path.exists(financial_path) or not os.path.exists(pd_path):
            raise FileNotFoundError(
                f"Raw data files not found: {financial_path} or {pd_path}"
            )

        df_fin = pd.read_csv(financial_path)
        df_pd = pd.read_csv(pd_path)

        # 1. Aggregate Financials: Get latest year per company
        # Sort by year descending, then drop duplicates keeping first (latest)
        df_fin_latest = df_fin.sort_values(
            ["id_empresa", "ano"], ascending=[True, False]
        ).drop_duplicates(subset=["id_empresa"], keep="first")

        # 2. Aggregate PD: Group by ID and take mean
        # We only want to mean the numeric columns, excluding ID from the mean operation but using it as key
        numeric_cols_pd = df_pd.select_dtypes(include=[np.number]).columns.tolist()
        if "id_empresa" in numeric_cols_pd:
            numeric_cols_pd.remove(
                "id_empresa"
            )  # Remove it so we don't average usage of ID

        df_pd_agg = df_pd.groupby("id_empresa")[numeric_cols_pd].mean().reset_index()
        # Ensure id_empresa is int after mean if it became float
        df_pd_agg["id_empresa"] = df_pd_agg["id_empresa"].astype(int)

        # 3. Merge
        df_merged = pd.merge(df_fin_latest, df_pd_agg, on="id_empresa", how="inner")

        logger.info(
            f"Financials Raw: {len(df_fin)} -> Aggregated: {len(df_fin_latest)}"
        )
        logger.info(f"PD Raw: {len(df_pd)} -> Aggregated: {len(df_pd_agg)}")
        logger.info(f"Merged Final Dimensions: {df_merged.shape}")

        return df_merged

    def initiate_data_ingestion(self):
        """
        Executed the data ingestion process from raw files.
        """
        logger.info("Entered the data ingestion method or component")
        try:
            # Paths to Raw Files
            train_fin_path = (
                self.config.source_data_dir / self.config.financial_data_file
            )
            train_pd_path = self.config.source_data_dir / self.config.pd_data_file

            val_fin_path = str(train_fin_path).replace("training", "validation")
            val_pd_path = str(train_pd_path).replace("training", "validation")

            # 1. Process Training Data
            df_train_raw = self._load_and_merge_raw_data(train_fin_path, train_pd_path)
            # Use imported function instead of method
            df_train = engineer_features(df_train_raw)

            # 2. Process Validation Data
            df_val_raw = self._load_and_merge_raw_data(val_fin_path, val_pd_path)
            # Use imported function instead of method
            df_val = engineer_features(df_val_raw)

            # 3. Consolidate and Re-Split?
            # The params.yaml specifies split sizes. It's safer to concat and use standard split logic
            # to ensure we follow the experiment's configured split ratios exactly.
            logger.info(
                "Consolidating Train and Validation sets for standardized splitting"
            )
            df_full = pd.concat([df_train, df_val], ignore_index=True)

            # 4. Perform Split with Stratification Logic
            test_val_ratio = self.config.val_size + self.config.test_size
            strat_col = (
                df_full[self.config.target_column]
                if self.config.target_column in df_full.columns
                else None
            )

            # --- First Split: Train vs Temp (Test + Val) ---
            try:
                # Attempt stratified split
                train_set, temp_set = train_test_split(
                    df_full,
                    test_size=test_val_ratio,
                    random_state=self.config.random_state,
                    stratify=strat_col,
                )
                logger.info("First split (Train/Temp) stratified successfully.")
            except ValueError as e:
                # Fallback to random if class count is too small (e.g., < 2 samples)
                logger.warning(
                    f"Stratified split failed for Train/Temp (likely too few positive samples): {e}. Falling back to random split."
                )
                train_set, temp_set = train_test_split(
                    df_full,
                    test_size=test_val_ratio,
                    random_state=self.config.random_state,
                    stratify=None,
                )

            # --- Second Split: Temp -> Val + Test ---
            # Recalculate strat_col for temp_set
            strat_col_temp = (
                temp_set[self.config.target_column]
                if self.config.target_column in temp_set.columns
                else None
            )
            test_ratio_relative = self.config.test_size / test_val_ratio

            try:
                # Attempt stratified split
                val_set, test_set = train_test_split(
                    temp_set,
                    test_size=test_ratio_relative,
                    random_state=self.config.random_state,
                    stratify=strat_col_temp,
                )
                logger.info("Second split (Val/Test) stratified successfully.")
            except ValueError as e:
                # Fallback to random
                logger.warning(
                    f"Stratified split failed for Val/Test (likely only 1 positive sample left): {e}. Falling back to random split."
                )
                val_set, test_set = train_test_split(
                    temp_set,
                    test_size=test_ratio_relative,
                    random_state=self.config.random_state,
                    stratify=None,
                )

            # 5. Save Artifacts
            # Ensure output dir exists
            os.makedirs(self.config.unzip_dir, exist_ok=True)

            train_path = self.config.unzip_dir / "train.csv"
            val_path = self.config.unzip_dir / "val.csv"
            test_path = self.config.unzip_dir / "test.csv"
            # Select final columns to match schema implicitly (dropping raw Spanish cols that aren't renamed)
            # We keep all columns for now, including calculated ones.

            train_set.to_csv(train_path, index=False)
            val_set.to_csv(val_path, index=False)
            test_set.to_csv(test_path, index=False)

            logger.info(f"Ingestion completed. Files saved to {self.config.unzip_dir}")
            logger.info(
                f"Train Shape: {train_set.shape}, Val Shape: {val_set.shape}, Test Shape: {test_set.shape}"
            )

        except Exception as e:
            logger.error(f"Error in data ingestion: {str(e)}")
            raise CustomException(e, sys)


if __name__ == "__main__":
    try:
        config_manager = ConfigurationManager()
        data_ingestion_config = config_manager.get_data_ingestion_config()
        data_ingestion = DataIngestion(config=data_ingestion_config)
        data_ingestion.initiate_data_ingestion()
    except Exception as e:
        logger.error(CustomException(e, sys))
