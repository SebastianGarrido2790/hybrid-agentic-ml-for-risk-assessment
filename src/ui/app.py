"""
Streamlit User Interface for the Agentic Credit Risk Assessment System (ACRAS).

This application serves as the user-facing frontend for the agentic reasoning engine.
"""

from typing import cast

import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage

import src.agents.config as config_module
from src.agents.graph import app as agent_app
from src.ui.components import render_header, render_sidebar, render_welcome_state
from src.ui.data_loader import initialize_session_state, load_company_list
from src.ui.styles import apply_custom_css, create_gauge_chart
from src.ui.utils import extract_risk_score
from src.utils.pdf_generator import generate_pdf_report

# 1. Configuration & Styling
st.set_page_config(
    page_title="ACRAS - Intelligence Suite",
    layout="wide",
    page_icon="💎",
    initial_sidebar_state="expanded",
)
apply_custom_css()
initialize_session_state()

# 2. Data Loading
df_companies = load_company_list()
settings = config_module.get_agent_settings()

# 3. UI Layout
render_header()
selected_id, submit_btn = render_sidebar(df_companies)

# 4. Agent Execution Flow
if submit_btn and selected_id:
    prompt = f"Please assess credit risk for Company ID {selected_id}."
    from src.agents.graph import AgentState

    initial_state = cast(
        AgentState,
        {
            "messages": [HumanMessage(content=prompt)],
            "company_id": str(selected_id),
        },
    )

    # Clear previous result while running
    st.session_state.assessment_result = None
    st.session_state.pdf_bytes = None
    st.session_state.reasoning_log = []
    st.session_state.used_fallback_lite = False

    st.markdown("### 📋 Intelligence Report")
    with st.status("**Agent Cluster Synchronization**", expanded=True) as status:
        try:
            for step in agent_app.stream(initial_state):
                for node_name, node_output in step.items():
                    messages = node_output.get("messages", [])
                    if not messages:
                        continue

                    for msg in messages:
                        # Identify Agent Label
                        agent_map = {
                            "financial_analyst": "📊 **Analyst**",
                            "data_scientist": "🔬 **Scientist**",
                            "orchestrator": "👔 **Director**",
                        }
                        agent_label = agent_map.get(node_name, "🤖 Agent")

                        # Handle Fallback / Info Messages
                        if isinstance(msg, SystemMessage) and any(
                            icon in str(msg.content) for icon in ["🔄", "⚠️", "🚨"]
                        ):
                            log_txt = f"{agent_label} → {msg.content}"
                            status.write(log_txt)
                            if "2nd Fallback" in str(msg.content):
                                st.session_state.used_fallback_lite = True
                            st.session_state.reasoning_log.append(
                                {"type": "info", "msg": log_txt}
                            )
                            continue

                        # Handle Tool Calls
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                m_txt = f"{agent_label} → Executing `{tc['name']}`"
                                status.write(m_txt)
                                st.session_state.reasoning_log.append(
                                    {"type": "tool", "msg": m_txt}
                                )

                        # Handle Final Result (Orchestrator)
                        elif msg.content:
                            if node_name == "orchestrator":
                                st.session_state.assessment_result = str(msg.content)
                                st.session_state.risk_score = extract_risk_score(
                                    st.session_state.assessment_result
                                )
                                st.session_state.last_company_id = selected_id
                                m_txt = f"{agent_label} → Compiling Final Directive..."
                                status.write(m_txt)
                                st.session_state.reasoning_log.append(
                                    {"type": "info", "msg": m_txt}
                                )
                            else:
                                m_txt = f"{agent_label} → Intelligence Update Captured."
                                status.write(m_txt)
                                st.session_state.reasoning_log.append(
                                    {
                                        "type": "expander",
                                        "msg": m_txt,
                                        "node_name": node_name,
                                        "content": msg.content,
                                    }
                                )
                                with st.expander(f"Access {node_name} logs"):
                                    st.write(msg.content)

            # Generate PDF automatically in memory
            try:
                provider_nick = settings.DEFAULT_LLM_PROVIDER.lower()
                if st.session_state.get("used_fallback_lite"):
                    provider_nick += "-lite"

                filename = f"ACRAS_Report_{selected_id}_{provider_nick}.pdf"
                pdf_bytes = generate_pdf_report(
                    str(st.session_state.assessment_result),
                    filename=filename,
                    save_to_disk=False,
                )
                st.session_state.pdf_bytes = pdf_bytes
            except Exception as pdf_err:
                st.session_state.reasoning_log.append(
                    {"type": "info", "msg": f"⚠️ PDF readiness failed: {pdf_err}"}
                )

            status.update(
                label="✨ **Analysis Synthesized**", state="complete", expanded=False
            )
            st.rerun()

        except Exception as e:
            status.update(label="🚨 **Critical Failure**", state="error")
            st.error(f"Stack Trace: {e}")

# 5. Results Display
if st.session_state.assessment_result:
    col_rep, col_dash = st.columns([1.5, 1])

    with col_rep:
        st.markdown(f"### 📋 Analysis for Company {st.session_state.last_company_id}")
        if st.session_state.reasoning_log:
            with st.expander("🔍 **Agent Cluster Synchronization Logs**"):
                for log in st.session_state.reasoning_log:
                    if log["type"] == "expander":
                        st.write(log["msg"])
                        with st.expander(f"Access {log['node_name']} logs"):
                            st.write(log["content"])
                    else:
                        st.write(log["msg"])
        st.markdown(st.session_state.assessment_result)

    with col_dash:
        st.markdown("### ⚡ Analytics Dashboard")
        score = st.session_state.risk_score
        st.plotly_chart(create_gauge_chart(score), width="stretch")

        # Decision Logic
        if score >= 70:
            st.error(f"### 🚩 REJECT\nRisk Level: **High** ({score:.1f})")
        elif score >= 30:
            st.warning(f"### ⚠️ REVIEW\nRisk Level: **Moderate** ({score:.1f})")
        else:
            st.success(f"### ✅ APPROVE\nRisk Level: **Low** ({score:.1f})")

        # Download Action
        st.markdown("---")
        if st.session_state.get("pdf_bytes"):
            provider_nick = settings.DEFAULT_LLM_PROVIDER.lower()
            if st.session_state.get("used_fallback_lite"):
                provider_nick += "-lite"

            st.download_button(
                label="📥 Download Executive PDF",
                data=cast(bytes, st.session_state.pdf_bytes),
                file_name=f"ACRAS_Report_{st.session_state.last_company_id}_{provider_nick}.pdf",
                mime="application/pdf",
                width="stretch",
            )
        else:
            st.warning("⚠️ Report preparation partial. PDF not available.")

elif not submit_btn and not st.session_state.assessment_result:
    render_welcome_state(df_companies)

elif submit_btn and not selected_id:
    st.warning("Please select a target entity.")
