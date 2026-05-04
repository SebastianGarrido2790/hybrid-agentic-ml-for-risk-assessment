"""
Data loading and session state management for the ACRAS UI.
"""

from pathlib import Path

import pandas as pd
import streamlit as st


@st.cache_data
def load_company_list() -> pd.DataFrame:
    """
    Load the list of companies from the processed validation dataset.

    Returns:
        pd.DataFrame: A DataFrame containing company IDs and key financial metrics.
    """
    try:
        # Resolve data path relative to the project root
        base_dir = Path(__file__).resolve().parent.parent.parent
        data_path = base_dir / "artifacts" / "data_ingestion" / "val.csv"

        if not data_path.exists():
            return pd.DataFrame()

        df = pd.read_csv(data_path)
        if "id_empresa" not in df.columns:
            return pd.DataFrame()

        return df.drop_duplicates(subset=["id_empresa"])
    except Exception as e:
        st.error(f"Failed to load company database: {e}")
        return pd.DataFrame()


def initialize_session_state() -> None:
    """Initialize all necessary session state variables for the application."""
    if "assessment_result" not in st.session_state:
        st.session_state.assessment_result = None
    if "risk_score" not in st.session_state:
        st.session_state.risk_score = 50.0
    if "last_company_id" not in st.session_state:
        st.session_state.last_company_id = None
    if "pdf_bytes" not in st.session_state:
        st.session_state.pdf_bytes = None
    if "reasoning_log" not in st.session_state:
        st.session_state.reasoning_log = []
    if "used_fallback_lite" not in st.session_state:
        st.session_state.used_fallback_lite = False
