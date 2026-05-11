"""
Unit tests for UI styles.
"""

from unittest.mock import patch

import plotly.graph_objects as go

from src.ui.styles import apply_custom_css, create_gauge_chart


def test_apply_custom_css():
    """Test applying CSS."""
    with patch("streamlit.markdown") as mock_md:
        apply_custom_css()
        mock_md.assert_called_once()


def test_create_gauge_chart():
    """Test gauge chart creation."""
    fig = create_gauge_chart(75.0)
    assert isinstance(fig, go.Figure)
    # Check if value is set correctly
    assert fig.data[0].value == 75.0
