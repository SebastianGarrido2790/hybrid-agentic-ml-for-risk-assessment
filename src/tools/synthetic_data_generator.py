"""
Synthetic Data Generator Tool.

This module generates synthetic financial data for distressed companies (defaults)
to address class imbalance. It combines the original raw data with generated
samples and saves the result to data/processed, keeping the raw data untouched.
"""

import pandas as pd
import numpy as np
import os
import sys
from src.utils.exception import CustomException


def generate_synthetic_data(n_samples=50):
    """
    Generates synthetic data for distressed companies (defaults).

    Args:
        n_samples (int): Number of synthetic samples to generate.

    Returns:
        tuple: (financials_df, pd_table_df)
    """
    np.random.seed(42)

    # Starting ID after the last real one (assumed 450)
    start_id = 1000

    # Financials
    ids = np.arange(start_id, start_id + n_samples)
    years = np.random.choice([2023, 2024], size=n_samples)

    # Distressed Logic:
    # Low/Negative EBITDA
    ingresos = np.random.uniform(500000, 2000000, n_samples)
    ebitda = ingresos * np.random.uniform(
        -0.15, 0.05, n_samples
    )  # mostly negative to low positive margin

    # High Debt (DE > 2)
    patrimonio = ingresos * np.random.uniform(0.1, 0.3, n_samples)
    pasivos = patrimonio * np.random.uniform(2.0, 5.0, n_samples)
    activos = pasivos + patrimonio

    # Low Liquidity
    cuentas_pagar = pasivos * 0.4
    quick_assets = cuentas_pagar * np.random.uniform(
        0.5, 0.9, n_samples
    )  # Current ratio < 0.9
    caja = quick_assets * 0.2
    cuentas_cobrar = quick_assets * 0.4
    inventario = quick_assets * 0.4

    # Other
    gastos_intereses = pasivos * 0.08

    financials = pd.DataFrame(
        {
            "id_empresa": ids,
            "ano": years,
            "ingresos": ingresos,
            "ebitda": ebitda,
            "activos_totales": activos,
            "pasivos_totales": pasivos,
            "patrimonio": patrimonio,
            "caja": caja,
            "gastos_intereses": gastos_intereses,
            "cuentas_cobrar": cuentas_cobrar,
            "inventario": inventario,
            "cuentas_pagar": cuentas_pagar,
        }
    )

    # PD Table
    # High risk indicators
    pd_table = pd.DataFrame(
        {
            "id_empresa": ids,
            "riesgo_sector": np.random.uniform(3.0, 5.0, n_samples),  # High risk sector
            "anos_operando": np.random.randint(1, 5, n_samples),  # Young companies
            "ratio_mora": np.random.uniform(0.1, 0.4, n_samples),  # High delinquency
            "ratio_utilizacion": np.random.uniform(
                0.8, 1.0, n_samples
            ),  # Maxed out credit lines
            "crecimiento_ventas": np.random.uniform(
                -0.2, 0.0, n_samples
            ),  # Shrinking sales
            "margen_beneficio": ebitda / ingresos,  # Consistent with financials
            "score_buro": np.random.randint(300, 550, n_samples),  # Low bureau score
            "default_12m": 1,  # TARGET = 1
            "pd_verdadera": np.random.uniform(0.15, 0.50, n_samples),  # High PD
        }
    )

    return financials, pd_table


if __name__ == "__main__":
    try:
        # Paths
        raw_fin_path = "data/raw/financial_statements_training.csv"
        raw_pd_path = "data/raw/pd_training.csv"
        processed_dir = "data/processed"
        os.makedirs(processed_dir, exist_ok=True)

        proc_fin_path = os.path.join(processed_dir, "financial_statements_training.csv")
        proc_pd_path = os.path.join(processed_dir, "pd_training.csv")

        if os.path.exists(raw_fin_path) and os.path.exists(raw_pd_path):
            print(f"Loading original raw data from {raw_fin_path}...")
            df_fin_raw = pd.read_csv(raw_fin_path)
            df_pd_raw = pd.read_csv(raw_pd_path)

            print("Generating synthetic data...")
            syn_fin, syn_pd = generate_synthetic_data(50)

            print("Combining original and synthetic data...")
            df_fin_combined = pd.concat([df_fin_raw, syn_fin], ignore_index=True)
            df_pd_combined = pd.concat([df_pd_raw, syn_pd], ignore_index=True)

            print(f"Saving augmented data to {processed_dir}...")
            df_fin_combined.to_csv(proc_fin_path, index=False)
            df_pd_combined.to_csv(proc_pd_path, index=False)

            # Also copy validation data to processed to maintain consistent source path for ingestion
            val_fin_raw = "data/raw/financial_statements_validation.csv"
            val_pd_raw = "data/raw/pd_validation.csv"
            if os.path.exists(val_fin_raw):
                pd.read_csv(val_fin_raw).to_csv(
                    os.path.join(processed_dir, "financial_statements_validation.csv"),
                    index=False,
                )
            if os.path.exists(val_pd_raw):
                pd.read_csv(val_pd_raw).to_csv(
                    os.path.join(processed_dir, "pd_validation.csv"), index=False
                )

            print("Success! Augmented dataset created in data/processed.")
        else:
            print("Error: Raw data files not found in data/raw.")
    except Exception as e:
        raise CustomException(e, sys)
