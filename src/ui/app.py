"""
Streamlit User Interface for the Agentic Credit Risk Assessment System (ACRAS).

This application serves as the user-facing frontend for the agentic reasoning engine.
It allows Risk Managers to:
1. Select a target company from the database.
2. Trigger the Multi-Agent System (Financial Analyst -> Data Scientist -> CRO).
3. Visualize the "Chain of Thought" (tool calls and reasoning steps).
4. View a structured Risk Assessment Report and a Risk Score gauge.
5. Download the report as a PDF.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from langchain_core.messages import HumanMessage
from src.agents.graph import app as agent_app
from src.utils.pdf_generator import generate_pdf_report
import re
from pathlib import Path

# Page Config
st.set_page_config(
    page_title="ACRAS - Intelligence Suite",
    layout="wide",
    page_icon="💎",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Premium Look ---
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


# Title and Header
st.title("🏦 ACRAS Intelligence Suite")
st.markdown("#### *Advanced Agentic Credit Risk & Analysis System*")
st.markdown("---")


# --- Load Company Data ---
@st.cache_data
def load_company_list():
    try:
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


df_companies = load_company_list()

# --- Session State Initialization ---
if "assessment_result" not in st.session_state:
    st.session_state.assessment_result = None
if "risk_score" not in st.session_state:
    st.session_state.risk_score = 50.0
if "last_company_id" not in st.session_state:
    st.session_state.last_company_id = None

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 📊 Control Panel")

    if not df_companies.empty:
        company_options = df_companies["id_empresa"].unique()
        selected_id = st.selectbox("🎯 Target Entity ID", company_options)

        # Show detailed info cards in sidebar
        company_row = df_companies[df_companies["id_empresa"] == selected_id].iloc[0]

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
            st.rerun()

    st.caption("Version 1.1 - Persistence Enabled")


# --- Helper Functions ---
def extract_risk_score(text):
    """Extracts the risk score from the text."""
    match = re.search(r"(?:Risk )?Score:\*{0,2}\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if match:
        score = float(match.group(1))
        if score <= 1.0:
            score *= 100
        return score
    return 50.0


def create_gauge_chart(score):
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


# --- Main Flow ---
if submit_btn and selected_id:
    prompt = f"Please assess credit risk for Company ID {selected_id}."
    initial_state = {
        "messages": [HumanMessage(content=prompt)],
        "company_id": str(selected_id),
    }

    # Clear previous result while running
    st.session_state.assessment_result = None

    # Layout: Report Left, Dashboard Right
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown("### 📋 Intelligence Report")

        with st.status("**Agent Cluster Synchronization**", expanded=True) as status:
            try:
                for step in agent_app.stream(initial_state):
                    for node_name, node_output in step.items():
                        messages = node_output.get("messages", [])
                        if not messages:
                            continue

                        last_msg = messages[-1]

                        # Identify Agent
                        agent_label = "🤖 Agent"
                        if node_name == "financial_analyst":
                            agent_label = "📊 **Analyst**"
                        elif node_name == "data_scientist":
                            agent_label = "🔬 **Scientist**"
                        elif node_name == "orchestrator":
                            agent_label = "👔 **Director**"

                        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                            for tc in last_msg.tool_calls:
                                status.write(
                                    f"{agent_label} → Executing `{tc['name']}`"
                                )
                        elif last_msg.content:
                            if node_name == "orchestrator":
                                st.session_state.assessment_result = str(
                                    last_msg.content
                                )
                                st.session_state.risk_score = extract_risk_score(
                                    st.session_state.assessment_result
                                )
                                st.session_state.last_company_id = selected_id
                                status.write(
                                    f"{agent_label} → Compiling Final Directive..."
                                )
                            else:
                                status.write(
                                    f"{agent_label} → Intelligence Update Captured."
                                )
                                with st.expander(f"Access {node_name} logs"):
                                    st.write(last_msg.content)

                status.update(
                    label="✨ **Analysis Synthesized**",
                    state="complete",
                    expanded=False,
                )
                st.rerun()  # Rerun to enter the "Results Display" state permanently

            except Exception as e:
                status.update(label="🚨 **Critical Failure**", state="error")
                st.error(f"Stack Trace: {e}")

# Display Results from Session State
if st.session_state.assessment_result:
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown(f"### 📋 Analysis for Company {st.session_state.last_company_id}")
        st.markdown(st.session_state.assessment_result)

    with col2:
        st.markdown("### ⚡ Analytics Dashboard")
        score = st.session_state.risk_score
        st.plotly_chart(create_gauge_chart(score), width="stretch")

        # Decision Logic Box
        if score >= 70:
            st.error(f"### 🚩 REJECT\nRisk Level: **High** ({score:.1f})")
        elif score >= 30:
            st.warning(f"### ⚠️ REVIEW\nRisk Level: **Moderate** ({score:.1f})")
        else:
            st.success(f"### ✅ APPROVE\nRisk Level: **Low** ({score:.1f})")

        # Document Action
        st.markdown("---")
        try:
            pdf_path = generate_pdf_report(
                st.session_state.assessment_result,
                filename=f"ACRAS_Report_{st.session_state.last_company_id}.pdf",
            )
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                label="📥 Download Executive PDF",
                data=pdf_bytes,
                file_name=f"ACRAS_Report_{st.session_state.last_company_id}.pdf",
                mime="application/pdf",
                width="stretch",
            )
        except Exception as e:
            st.info(f"PDF Engine Offline: {e}")

elif not submit_btn:
    # Welcome State
    st.info("👈 Select a Company ID from the Control Panel to begin the assessment.")

    # Showcase stats
    if not df_companies.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Database Coverage", len(df_companies), "Records")
        c2.metric("Median Revenue", f"${df_companies['ingresos'].median():,.0f}")
        c3.metric("System Status", "Ready", delta="Optimal", delta_color="normal")

elif submit_btn and not selected_id:
    st.warning("Please select a target entity.")
