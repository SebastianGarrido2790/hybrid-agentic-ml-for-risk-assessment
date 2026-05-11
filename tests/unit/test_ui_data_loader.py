"""
Unit tests for UI data loader.
"""

from unittest.mock import MagicMock, patch

import pandas as pd

from src.ui.data_loader import (
    clear_assessment_state,
    initialize_session_state,
    load_company_list,
)


def test_load_company_list_missing():
    """Test loading company list when file is missing."""
    with patch("pathlib.Path.exists", return_value=False):
        df = load_company_list()
        assert df.empty


def test_load_company_list_success():
    """Test successful company list loading."""
    mock_df = pd.DataFrame({"id_empresa": [1, 1, 2], "value": [10, 10, 20]})

    # We MUST patch cache_data BEFORE importing or using the function if possible,
    # but since it's already decorated, we can try to patch the underlying function __wrapped__
    # or just patch the dependencies and ignore the cache.
    with (
        patch("src.ui.data_loader.Path.exists", return_value=True),
        patch("pandas.read_csv", return_value=mock_df),
    ):
        # Access the original function if it's cached
        func = load_company_list
        if hasattr(load_company_list, "__wrapped__"):
            func = load_company_list.__wrapped__

        df = func()
        assert len(df) == 2  # duplicates dropped
        assert 1 in df["id_empresa"].values
        assert 2 in df["id_empresa"].values


def test_initialize_session_state():
    """Test initialization of streamlit session state."""
    mock_state = MagicMock()
    # Mock __contains__ for 'if key not in st.session_state'
    mock_state.__contains__.return_value = False

    with patch("streamlit.session_state", mock_state):
        initialize_session_state()
        # Check if set appropriately (using dot or bracket notation)
        assert mock_state.risk_score == 50.0


def test_clear_assessment_state():
    """Test clearing of streamlit session state."""
    mock_state = MagicMock()
    with patch("streamlit.session_state", mock_state):
        clear_assessment_state()
        assert mock_state.assessment_result is None
        assert mock_state.risk_score == 50.0
