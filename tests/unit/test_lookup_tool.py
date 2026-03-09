"""
Unit tests for lookup_tool.py.

This module tests the data retrieval tools used by the AI Agent to fetch
company data from the database.
"""

from unittest.mock import patch

import pandas as pd

from src.agents.tools.lookup_tool import fetch_company_data


@patch("src.agents.tools.lookup_tool.Path.exists")
@patch("src.agents.tools.lookup_tool.pd.read_csv")
def test_fetch_company_data_success(mock_read_csv, mock_exists):
    """
    Tests successful data retrieval for a given company ID.
    """
    mock_exists.return_value = True
    mock_df = pd.DataFrame(
        {"id_empresa": [1, 2], "metric_a": [10, 20], "target": [0, 1]}
    )
    mock_read_csv.return_value = mock_df

    result = fetch_company_data.invoke({"company_id": 1})
    assert "metric_a" in result
    assert "target" not in result


@patch("src.agents.tools.lookup_tool.Path.exists")
def test_fetch_company_data_not_found(mock_exists):
    mock_exists.return_value = False
    result = fetch_company_data.invoke({"company_id": 1})
    assert "Error: Database file not found" in result


@patch("src.agents.tools.lookup_tool.Path.exists")
@patch("src.agents.tools.lookup_tool.pd.read_csv")
def test_fetch_company_data_id_not_found(mock_read_csv, mock_exists):
    mock_exists.return_value = True
    mock_df = pd.DataFrame({"id_empresa": [2], "metric_a": [20]})
    mock_read_csv.return_value = mock_df

    result = fetch_company_data.invoke({"company_id": 1})
    assert "Error: Company ID 1 not found." in result
