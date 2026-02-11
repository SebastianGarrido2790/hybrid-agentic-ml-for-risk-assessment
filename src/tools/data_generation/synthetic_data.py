"""
Synthetic Data Generation Tool.

This module provides functionality to generate synthetic financial data for testing
the Credit Risk Assessment agents and pipeline.
"""

import numpy as np
import pandas as pd
from typing import Optional


def generate_synthetic_data(
    n_samples: int = 1000, random_seed: Optional[int] = 42
) -> pd.DataFrame:
    """
    Generates a synthetic dataset for credit risk assessment.

    Args:
        n_samples (int): Number of samples to generate.
        random_seed (int): Seed for reproducibility.

    Returns:
        pd.DataFrame: DataFrame containing features and target labels.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    data = {
        "revenue_growth": np.random.normal(0.05, 0.1, n_samples),  # 5% avg growth
        "ebitda_margin": np.random.normal(0.15, 0.05, n_samples),  # 15% avg margin
        "debt_to_equity": np.random.normal(1.5, 0.5, n_samples),  # 1.5 avg D/E
        "current_ratio": np.random.normal(1.2, 0.3, n_samples),  # 1.2 avg current ratio
        "sector_risk_score": np.random.randint(1, 10, n_samples),  # 1-10 sector risk
        "years_operating": np.random.randint(1, 50, n_samples),  # Years in business
    }

    df = pd.DataFrame(data)

    # Calculate Logic: Low margins + High Debt + High Sector Risk -> Higher Default Probability
    risk_score = (
        -2 * df["ebitda_margin"]
        + 0.5 * df["debt_to_equity"]
        + 0.1 * df["sector_risk_score"]
        - 0.05 * df["years_operating"]
    )

    # Sigmoid function to convert risk score to probability and then to binary class
    prob = 1 / (1 + np.exp(-risk_score))

    df["default_probability"] = prob
    df["target"] = (prob > 0.5).astype(int)

    return df


if __name__ == "__main__":
    # Test execution
    df = generate_synthetic_data(n_samples=100)
    print(f"Generated {len(df)} samples.")
    print(df.head())
