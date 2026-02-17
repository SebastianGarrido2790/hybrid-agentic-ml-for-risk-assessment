"""
Global Pytest Fixtures.

This module provides shared fixtures for the entire test suite,
including sample data generation for financial and probability of default (PD) records.
"""

import sys
import os
import pytest
import pandas as pd


# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


@pytest.fixture
def sample_financial_data():
    """Returns a sample dataframe mimicking financial data."""
    data = {
        "id_empresa": [1, 1, 2, 3],
        "ano": [2022, 2021, 2022, 2022],
        "ingresos": [1000, 900, 500, 2000],
        "ebitda": [200, 150, 50, 400],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_pd_data():
    """Returns a sample dataframe mimicking PD data."""
    data = {
        "id_empresa": [1, 1, 2, 3],
        "default_prob": [0.05, 0.04, 0.1, 0.02],
        "risk_score": [10, 12, 50, 5],
    }
    return pd.DataFrame(data)
