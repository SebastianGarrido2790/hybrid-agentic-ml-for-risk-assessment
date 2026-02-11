"""
Synthetic Data Generation Tool.

This module provides functionality to generate synthetic financial data for testing
the Credit Risk Assessment agents and pipeline.
"""

import numpy as np
import pandas as pd
from typing import Optional
from faker import Faker
import random


def generate_synthetic_data(
    n_samples: int = 1000, random_seed: Optional[int] = 42
) -> pd.DataFrame:
    """
    Generates a synthetic dataset for credit risk assessment with diverse data types.

    Args:
        n_samples (int): Number of samples to generate.
        random_seed (int): Seed for reproducibility.

    Returns:
        pd.DataFrame: DataFrame containing features and target labels.
    """
    if random_seed is not None:
        np.random.seed(random_seed)
        random.seed(random_seed)
        Faker.seed(random_seed)

    fake = Faker()

    # predefined lists for categorical data
    sectors = [
        "Technology",
        "Healthcare",
        "Financials",
        "Consumer Discretionary",
        "Industrials",
        "Energy",
        "Utilities",
        "Real Estate",
        "Materials",
        "Telecommunications",
    ]

    regions = [
        "North America",
        "Europe",
        "Asia Pacific",
        "Latin America",
        "Middle East & Africa",
    ]

    data = {
        # Numerical
        "revenue_growth": np.random.normal(0.05, 0.1, n_samples),
        "ebitda_margin": np.random.normal(0.15, 0.05, n_samples),
        "debt_to_equity": np.random.normal(1.5, 0.5, n_samples),
        "current_ratio": np.random.normal(1.2, 0.3, n_samples),
        "sector_risk_score": np.random.randint(1, 10, n_samples),
        "years_operating": np.random.randint(1, 50, n_samples),
        # Categorical
        "industry_sector": [random.choice(sectors) for _ in range(n_samples)],
        "region": [random.choice(regions) for _ in range(n_samples)],
        # Boolean
        "is_publicly_traded": [random.choice([True, False]) for _ in range(n_samples)],
        "has_prior_default": [random.choice([True, False]) for _ in range(n_samples)],
        # High Cardinality
        "company_id": [fake.uuid4() for _ in range(n_samples)],
        "company_name": [fake.company() for _ in range(n_samples)],
        "tax_id": [fake.ein() for _ in range(n_samples)],
        # Text
        "risk_factors_report": [
            fake.paragraph(nb_sentences=3) for _ in range(n_samples)
        ],
        "analyst_notes": [fake.sentence(nb_words=10) for _ in range(n_samples)],
        # Date/Time
        "establishment_date": [
            fake.date_between(start_date="-50y", end_date="-1y")
            for _ in range(n_samples)
        ],
        "last_financial_report": [
            fake.date_between(start_date="-1y", end_date="today")
            for _ in range(n_samples)
        ],
    }

    df = pd.DataFrame(data)

    # Calculate Logic: Low margins + High Debt + High Sector Risk -> Higher Default Probability
    risk_score = (
        -2 * df["ebitda_margin"]
        + 0.5 * df["debt_to_equity"]
        + 0.1 * df["sector_risk_score"]
        - 0.05 * df["years_operating"]
    )

    # Add some noise from categorical/boolean factors
    risk_score += df["has_prior_default"].apply(lambda x: 0.5 if x else 0)
    risk_score += df["industry_sector"].apply(lambda x: 0.2 if x == "Energy" else 0)

    # Sigmoid function to convert risk score to probability and then to binary class
    prob = 1 / (1 + np.exp(-risk_score))

    df["default_probability"] = prob
    df["target"] = (prob > 0.5).astype(int)

    return df


if __name__ == "__main__":
    # Test execution
    df = generate_synthetic_data(n_samples=100)
    print(f"Generated {len(df)} samples.")
    print(df.info())
    print(df.head())
