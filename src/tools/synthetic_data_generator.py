"""
Synthetic Data Generator Tool.

This module generates synthetic financial data for distressed companies (defaults)
to address class imbalance. It uses probabilistic logic and introduces noise
to ensure the model learns realistic, non-deterministic patterns.
"""

import os
import sys

import numpy as np
import pandas as pd

from src.utils.exception import CustomException
from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_synthetic_data(n_samples: int = 50):
    """
    Generates synthetic data for companies with a probabilistic default target.
    Introduces entropy and class overlap to ensure realistic model metrics.

    Args:
        n_samples (int): Number of synthetic samples to generate.

    Returns:
        tuple: (financials_df, pd_table_df)
    """
    np.random.seed(42)

    # Starting ID after the last real one
    start_id = 1000
    ids = np.arange(start_id, start_id + n_samples)
    years = np.random.choice([2023, 2024], size=n_samples)

    # 1. Base Financials with High Variance (Noise)
    ingresos = np.random.uniform(300000, 3000000, n_samples)
    # ebitda_margin: mixed, but mostly low/negative
    ebitda_margin = np.random.uniform(-0.25, 0.10, n_samples)
    ebitda = ingresos * ebitda_margin

    # 2. Leverage with Noise
    # Most will have high debt, but some will have extreme debt
    patrimonio = ingresos * np.random.uniform(0.05, 0.4, n_samples)
    de_ratio = np.random.uniform(1.5, 6.0, n_samples)
    pasivos = patrimonio * de_ratio
    activos = pasivos + patrimonio

    # 3. Liquidity (Messy data)
    cuentas_pagar = pasivos * np.random.uniform(0.2, 0.6, n_samples)
    quick_ratio = np.random.uniform(0.3, 1.2, n_samples)
    quick_assets = cuentas_pagar * quick_ratio
    caja = quick_assets * np.random.uniform(0.05, 0.3, n_samples)
    cuentas_cobrar = quick_assets * np.random.uniform(0.3, 0.5, n_samples)
    inventario = quick_assets - caja - cuentas_cobrar

    gastos_intereses = pasivos * np.random.uniform(0.05, 0.12, n_samples)

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

    # 4. Probabilistic Target Generation (The "Entropy" Layer)
    # Default probability depends on Debt-to-Equity and EBITDA Margin
    # Logistic function: P(default) = 1 / (1 + exp(-(f(x))))
    # Higher DE and lower Margin -> higher P
    logit = (de_ratio - 3.5) * 1.5 - (ebitda_margin + 0.05) * 15
    prob_default = 1 / (1 + np.exp(-logit))

    # Add noise to the probability itself to simulate hidden factors
    prob_default = np.clip(prob_default + np.random.normal(0, 0.15, n_samples), 0, 1)

    # Randomly assign default based on probability (introduces class overlap)
    target = (np.random.random(n_samples) < prob_default).astype(int)

    # 5. PD Table
    pd_table = pd.DataFrame(
        {
            "id_empresa": ids,
            "riesgo_sector": np.random.uniform(2.5, 5.0, n_samples),
            "anos_operando": np.random.randint(1, 10, n_samples),
            "ratio_mora": np.random.uniform(0.05, 0.5, n_samples),
            "ratio_utilizacion": np.random.uniform(0.6, 1.1, n_samples),
            "crecimiento_ventas": np.random.uniform(-0.3, 0.1, n_samples),
            "margen_beneficio": ebitda / ingresos,
            "score_buro": np.random.randint(250, 650, n_samples),
            "default_12m": target,  # This is NO LONGER strictly 1
            "pd_verdadera": prob_default,  # For internal audit, should be dropped in training
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
            logger.info(f"Loading original raw data from {raw_fin_path}...")
            df_fin_raw = pd.read_csv(raw_fin_path)
            df_pd_raw = pd.read_csv(raw_pd_path)

            logger.info(
                "Generating realistic synthetic data with probabilistic noise..."
            )
            syn_fin, syn_pd = generate_synthetic_data(
                100
            )  # Increase count for better variance

            logger.info("Combining original and synthetic data...")
            df_fin_combined = pd.concat([df_fin_raw, syn_fin], ignore_index=True)
            df_pd_combined = pd.concat([df_pd_raw, syn_pd], ignore_index=True)

            logger.info(f"Saving augmented data to {processed_dir}...")
            df_fin_combined.to_csv(proc_fin_path, index=False)
            df_pd_combined.to_csv(proc_pd_path, index=False)

            # Copy validation data
            val_files = [
                "financial_statements_validation.csv",
                "pd_validation.csv",
            ]
            for vf in val_files:
                vpath = os.path.join("data/raw", vf)
                if os.path.exists(vpath):
                    pd.read_csv(vpath).to_csv(
                        os.path.join(processed_dir, vf), index=False
                    )

            logger.info(
                "Success! Realistic augmented dataset created in data/processed."
            )
        else:
            logger.error("Error: Raw data files not found in data/raw.")
    except Exception as e:
        raise CustomException(e, sys)
