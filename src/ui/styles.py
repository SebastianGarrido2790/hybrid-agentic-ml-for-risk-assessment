"""
Custom CSS and visualization styles for the ACRAS UI.
"""

import plotly.graph_objects as go
import streamlit as st


def apply_custom_css() -> None:
    """Apply premium look and feel CSS to the Streamlit app."""
    st.markdown(
        """
    <style>
        /* Main Background */
        .stApp {
            background: radial-gradient(circle at top right, #1e293b, #0f172a);
            color: #f8fafc;
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(255,255,255,0.1);
        }
        
        /* Metric Cards */
        div[data-testid="stMetricValue"] {
            font-size: 28px;
            color: #38bdf8;
        }
        
        /* Buttons */
        .stButton>button {
            border-radius: 8px;
            background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
            border: none;
            color: white;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: rgba(255,255,255,0.05) !important;
            border-radius: 8px !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def create_gauge_chart(score: float) -> go.Figure:
    """
    Create a premium Plotly gauge chart for risk visualization.

    Args:
        score: The risk score to visualize (0-100).

    Returns:
        A Plotly Figure object.
    """
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {"range": [None, 100], "tickwidth": 1, "tickcolor": "#94a3b8"},
                "bar": {"color": "#6366f1"},
                "steps": [
                    {"range": [0, 30], "color": "rgba(34, 197, 94, 0.2)"},
                    {"range": [30, 70], "color": "rgba(234, 179, 8, 0.2)"},
                    {"range": [70, 100], "color": "rgba(239, 68, 68, 0.2)"},
                ],
                "threshold": {
                    "line": {"color": "#f8fafc", "width": 4},
                    "thickness": 0.75,
                    "value": score,
                },
            },
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#f8fafc", "family": "Inter, sans-serif"},
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig
