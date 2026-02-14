"""
Script to analyze class distribution in the raw (original) and processed (augmented) datasets.

This utility loads the financial and PD data from both data/raw and data/processed,
merges them, and prints the distribution of defaults to verify
the impact of the synthetic data augmentation.
"""

import pandas as pd
import numpy as np
import sys
import os
from src.utils.exception import CustomException


def check_distribution(data_dir, label):
    """
    Analyzes the distribution of the target class in a given directory.

    Args:
        data_dir (str): Path to the directory containing the CSV files.
        label (str): Label for the output section.
    """
    try:
        fin_path = os.path.join(data_dir, "financial_statements_training.csv")
        pd_path = os.path.join(data_dir, "pd_training.csv")

        if not os.path.exists(fin_path) or not os.path.exists(pd_path):
            print(f"\n--- {label} (missing) ---")
            return

        df_fin = pd.read_csv(fin_path)
        df_pd = pd.read_csv(pd_path)

        # Merge logic matching the Data Ingestion component
        df_fin_latest = df_fin.sort_values(
            ["id_empresa", "ano"], ascending=[True, False]
        ).drop_duplicates(subset=["id_empresa"], keep="first")

        numeric_cols = df_pd.select_dtypes(include=[np.number]).columns.tolist()
        if "id_empresa" in numeric_cols:
            numeric_cols.remove("id_empresa")

        df_pd_agg = df_pd.groupby("id_empresa")[numeric_cols].mean().reset_index()

        merged = pd.merge(df_fin_latest, df_pd_agg, on="id_empresa")

        print(f"\n--- {label} ---")
        print(f"Total Unique Companies: {len(merged)}")
        print(
            f"Total Positive Samples (default_12m=1): {int(merged['default_12m'].sum())}"
        )

        pos_samples = merged[merged["default_12m"] == 1]
        pos_ratio = (len(pos_samples) / len(merged)) * 100 if len(merged) > 0 else 0
        print(f"Positive Sample Ratio: {pos_ratio:.2f}%")

        pos_ids = pos_samples["id_empresa"].tolist()
        if len(pos_ids) > 10:
            print(f"Positive Sample IDs (first 10): {pos_ids[:10]}...")
        else:
            print(f"Positive Sample IDs: {pos_ids}")

    except Exception as e:
        raise CustomException(e, sys)


if __name__ == "__main__":
    try:
        # Check both source directories
        check_distribution("data/raw", "ORIGINAL RAW DATA")
        check_distribution("data/processed", "AUGMENTED PROCESSED DATA")
    except Exception as e:
        print(e)
