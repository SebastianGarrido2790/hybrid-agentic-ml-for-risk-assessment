"""
Reusable UI components for the ACRAS Intelligence Suite.
"""

import importlib
from typing import Any

import pandas as pd
import streamlit as st

import src.agents.config as config_module


def render_header() -> None:
    """Render the application title and active model status."""
    st.title("🏦 ACRAS Intelligence Suite")
    col_title, col_info = st.columns([3, 1])
    with col_title:
        st.markdown("#### *Advanced Agentic Credit Risk & Analysis System*")

    with col_info:
        # Force reload of config module to reflect file changes in UI instantly
        importlib.reload(config_module)
        settings = config_module.get_agent_settings()

        provider = settings.DEFAULT_LLM_PROVIDER.upper()
        model = (
            settings.HF_MODEL
            if settings.DEFAULT_LLM_PROVIDER == "huggingface"
            else settings.GEMINI_POWER_MODEL
        )
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.05); padding: 5px 10px; border-radius: 5px; border-left: 3px solid #3b82f6; font-size: 0.8em;">
                <b>Active Intelligence:</b> {provider}<br>
                <span style="color: #94a3b8;">{model}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("---")


def render_sidebar(df_companies: pd.DataFrame) -> tuple[Any, bool]:
    """
    Render the sidebar with company selection and engine controls.

    Args:
        df_companies: DataFrame containing company records.

    Returns:
        The selected company ID, or None if no selection.
    """
    with st.sidebar:
        st.markdown("### 📊 Control Panel")

        if not df_companies.empty:
            company_options = df_companies["id_empresa"].unique()
            selected_id = st.selectbox("🎯 Target Entity ID", company_options)

            # Show detailed info cards in sidebar
            company_row = df_companies[df_companies["id_empresa"] == selected_id].iloc[
                0
            ]

            st.markdown("---")
            st.metric("Annual Revenue", f"${company_row['ingresos']:,.0f}")
            st.metric("EBITDA", f"${company_row['ebitda']:,.0f}")
            st.metric("Bureau Score", int(company_row["score_buro"]))

        else:
            st.error("Database not found.")
            selected_id = None

        st.markdown("---")
        st.markdown("🚀 **Engine Controls**")

        col_reset, col_submit = st.columns(2)

        with col_submit:
            submit_btn = st.button("Initiate", type="primary", width="stretch")

        with col_reset:
            if st.button("Reset", width="stretch"):
                st.session_state.assessment_result = None
                st.session_state.risk_score = 50.0
                st.session_state.last_company_id = None
                st.session_state.pdf_bytes = None
                st.session_state.reasoning_log = []
                st.session_state.used_fallback_lite = False
                st.rerun()

    st.caption("Version 1.1 - Persistence Enabled")
    return selected_id, submit_btn


def render_welcome_state(df_companies: pd.DataFrame) -> None:
    """Render the welcome message and summary statistics."""
    st.info("👈 Select a Company ID from the Control Panel to begin the assessment.")

    if not df_companies.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Database Coverage", len(df_companies), "Records")
        c2.metric("Median Revenue", f"${df_companies['ingresos'].median():,.0f}")
        c3.metric("System Status", "Ready", delta="Optimal", delta_color="normal")
