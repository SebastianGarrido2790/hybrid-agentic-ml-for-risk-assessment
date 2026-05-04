# ACRAS User Interface Guide

**Version:** 1.3 — Hardened Synthesis
**Date:** 2026-05-04 | **Repository:** `SebastianGarrido2790/hybrid-agentic-ml-for-risk-assessment`

---

## 1. Introduction

The **ACRAS Intelligence Suite** is a modular Streamlit application designed for Risk Managers. Following project modularity standards, the interface is decomposed into specialized modules to ensure maintainability and high-performance rendering:

- **`src/ui/app.py`**: The primary orchestrator and entry point.
- **`src/ui/components.py`**: Reusable UI elements (Headers, Sidebar, Welcome state).
- **`src/ui/styles.py`**: Custom CSS tokens and Plotly visualization logic.
- **`src/ui/data_loader.py`**: Dataset ingestion and session state initialization.
- **`src/ui/utils.py`**: Helper functions for risk score extraction and logic.

The application title bar reads:
> 🏦 **ACRAS Intelligence Suite** — *Advanced Agentic Credit Risk & Analysis System*

---

## 2. How to Run the App

### 2.1 Manual Launch (Two Terminals)

1. **Start the ML API Backend**
   Open a terminal and run the FastAPI prediction server:
   ```bash
   uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start the Streamlit Frontend**
   Open a *new* terminal window and run:
   ```bash
   uv run streamlit run src/ui/app.py
   ```

3. **Access the Dashboard**
   Open your browser at `http://localhost:8501`.

### 2.2 Single-Command Launch (`launch_acras.bat`)

The provided batch script automates the entire startup sequence in three steps:

```bat
.\launch_acras.bat
```

The script will:
1. **[1/3]** Run `uv sync --quiet` to ensure the environment matches `pyproject.toml`.
2. **[2/3]** Launch the FastAPI backend (`http://localhost:8000`) in a **minimized** `cmd` window titled `ACRAS-API`.
3. **[WAIT]** Stall for **5 seconds** for the API to initialize before connecting the UI.
4. **[3/3]** Launch the Streamlit frontend (`http://localhost:8501`) in the foreground.

> **Tip:** To stop the full system, close the `ACRAS-API` window in the taskbar, then press `Ctrl+C` in the main terminal.

### 2.3 Production Orchestration (Docker Compose)

For a production-elite deployment, ACRAS uses a unified Docker environment to orchestrate the API, UI, and MLflow services.

1. **Configure Environment**
   Ensure your `.env` file contains the required keys:
   ```dotenv
   GOOGLE_API_KEY=your_key
   HUGGINGFACEHUB_API_TOKEN=your_token
   ```

2. **Launch the Suite**
   Run the following command from the project root:
   ```bash
   docker-compose up --build
   ```

3. **Service Mapping**
   - **Streamlit UI:** `http://localhost:8501`
   - **FastAPI Backend:** `http://localhost:8000`
   - **MLflow Server:** `http://localhost:5000`

The suite uses **Docker Health Checks** to ensure the UI only initializes once the API is fully responsive, preventing "Connection Refused" errors during startup.

---

## 3. Global Hot-Swapping (Live Model Switching)

ACRAS supports **live LLM hot-swapping** without restarting the Streamlit application. The configuration lives in `src/agents/config.py`.

| Setting | Environment Variable | Default |
| :--- | :--- | :--- |
| Active Provider | `DEFAULT_LLM_PROVIDER` | `huggingface` |
| Primary HuggingFace Model | `HF_MODEL` | `Qwen/Qwen2.5-7B-Instruct` |
| Primary Gemini Model | `GEMINI_POWER_MODEL` | `gemini-2.5-flash` |
| Lite Fallback Model | `GEMINI_LITE_MODEL` | `gemini-2.5-flash-lite` |

**How to swap:**
1. Edit the desired value in `src/agents/config.py` (or update your `.env` file).
2. The **Active Intelligence** badge in the page header will reflect the change on the next Streamlit render — no restart required.
3. Click **Initiate** to run the agents immediately with the new configuration.

---

## 4. Key Interface Components

### 4.1 Page Header (Observability Badge)

Located in the top-right area of the main page, the **Active Intelligence** card displays:
- **Provider:** Current provider in uppercase (e.g., `GEMINI` or `HUGGINGFACE`).
- **Model:** The specific model name currently driving orchestration logic (e.g., `gemini-2.5-flash` or `Qwen/Qwen2.5-7B-Instruct`).

The badge is rendered as a styled HTML div with a left blue border and updates on every page render via `importlib.reload(config_module)`.

### 4.2 Control Panel (Left Sidebar)

| Element | Description |
| :--- | :--- |
| **🎯 Target Entity ID** | Dropdown (`st.selectbox`) to select a company from the `val.csv` database. |
| **Annual Revenue** | `st.metric` showing `ingresos` for the selected company. |
| **EBITDA** | `st.metric` showing `ebitda` for the selected company. |
| **Bureau Score** | `st.metric` showing `score_buro` for the selected company. |
| **Initiate** | Primary button (right column). Triggers the full multi-agent workflow. |
| **Reset** | Secondary button (left column). Clears `assessment_result`, `risk_score`, `pdf_bytes`, and `reasoning_log` from session state and reruns. |

> **Note:** The **Reset** button is in the *left* column and **Initiate** is in the *right* column of a two-column layout within the sidebar.

The sidebar footer displays: `Version 1.1 - Persistence Enabled`.

### 4.3 Welcome State (Idle Dashboard)

When no assessment has been run yet, the main panel displays an informational banner:

> 👈 *Select a Company ID from the Control Panel to begin the assessment.*

Below it, three summary metrics are shown inline:

| Metric | Value |
| :--- | :--- |
| **Database Coverage** | Number of unique companies in `val.csv` |
| **Median Revenue** | Median `ingresos` across all companies |
| **System Status** | `Ready` / `Optimal` |

### 4.4 Agent Cluster Synchronization Logs (Live — During Run)

While an assessment is running, the left column (`col1`) renders a `st.status` block labeled **"Agent Cluster Synchronization"** (expanded by default). This block streams real-time messages:

- **Tool call logs:** `📊 **Analyst** → Executing \`fetch_company_data\``
- **Fallback logs:** `🔄 Falling back to 1st Fallback (gemini-2.5-flash)...`
- **Warning logs:** `⚠️ Primary (qwen/qwen2.5-7b-instruct) failed.`
- **Guardrail logs:** `🚨 [SYSTEM] Deterministic Risk Advisory injected.` (if critical thresholds are breached).
- **Agent response logs:** `📊 **Analyst** → Intelligence Update Captured.` followed by an inline expander showing the agent's raw output.
- **Final log:** `👔 **Director** → Compiling Final Directive...`

On completion, the block collapses and updates its label to **"✨ Analysis Synthesized"**.

### 4.5 Results View (Post-Run — Persistent)

After the `st.rerun()`, the layout switches to a **two-column layout** `[1.5, 1]`:

**Left Column — Intelligence Report**
- Header: `### 📋 Analysis for Company {company_id}`
- Collapsed expander: `🔍 **Agent Cluster Synchronization Logs**` — contains the full replay of all log entries from the run.
- Full markdown rendering of the Director's final executive report (`st.session_state.assessment_result`).

**Right Column — Analytics Dashboard**
- Header: `### ⚡ Analytics Dashboard`
- **Risk Gauge:** A Plotly `go.Indicator` gauge chart (0–100 scale) with three color bands. Following Streamlit's latest API standards, charts are rendered with `width='stretch'` for maximum responsive fit.
  - 🟢 **0–30:** Low Risk (green zone)
  - 🟡 **30–70:** Moderate Risk (yellow zone)
  - 🔴 **70–100:** High Risk (red zone)
- **Decision Logic Box:**

  | Score Range | UI Element | Message |
  | :--- | :--- | :--- |
  | ≥ 70 | `st.error` | `🚩 REJECT — Risk Level: High` |
  | 30–69 | `st.warning` | `⚠️ REVIEW — Risk Level: Moderate` |
  | < 30 | `st.success` | `✅ APPROVE — Risk Level: Low` |

- **📥 Download Executive PDF** button (below a horizontal rule). Generates a PDF with the filename pattern:
  ```
  ACRAS_Report_{company_id}_{provider}.pdf
  # e.g., ACRAS_Report_489_gemini.pdf
  # e.g., ACRAS_Report_22_huggingface-lite.pdf  (if Lite fallback was used)
  ```
  If PDF generation failed, a `⚠️ Report preparation partial. PDF not available.` warning is displayed instead.

---

## 5. The Agent Cluster Workflow

The graph follows a **Sequential Relay** pattern with conditional tool-call loops:

```
START → financial_analyst ⇆ financial_tools → data_scientist ⇆ ml_tools → orchestrator → END
```

| UI Label | Graph Node | Focus | Key Deliverables |
| :--- | :--- | :--- | :--- |
| `📊 **Analyst**` | `financial_analyst` | Financial Health | Liquidity/Solvency ratios, key metric tables, per-metric risk ratings. |
| `🔬 **Scientist**` | `data_scientist` | ML Prediction | Probability of Default (PD), ML feature interpretation, quantitative tiering. |
| `👔 **Director**` | `orchestrator` | Executive Synthesis | High-authority synthesis of all specialist findings into a mandatory 6-section report. Incorporates **Deterministic Risk Guardrails** if critical ratios (Delinquency > 20% or Liquidity < 0.5) are detected. |

The node name shown in the log expanders matches the internal graph node key (e.g., `Access financial_analyst logs`).
The Orchestrator uses a **High-Adherence Prompting** pattern that merges role instructions and specialist findings into a single turn to prevent response truncation.

---

## 6. Resilience: 3-Tier Fallback Mechanism

Each agent invocation is governed by `invoke_with_fallback()`, which sequentially attempts three model tiers and surfaces status messages to the UI:

| Tier | Label | Model / Provider |
| :--- | :--- | :--- |
| **Primary** | `Primary` | Currently configured provider (`HF_MODEL` or `GEMINI_POWER_MODEL`) |
| **Fallback 1** | `1st Fallback` | Cross-provider switch (HuggingFace ↔ Gemini `GEMINI_POWER_MODEL`) |
| **Fallback 2** | `2nd Fallback` | `gemini-2.5-flash-lite` (high availability, low latency) |

When the **2nd Fallback** is triggered, the session flag `used_fallback_lite` is set to `True`, and the PDF filename is automatically suffixed with `-lite` to track which model produced the report.

---

## 7. Downloading Reports

Once the assessment is complete:
1. The PDF is automatically generated in-memory immediately after the Director's response is captured.
2. The **📥 Download Executive PDF** button appears in the **right column** of the Analytics Dashboard. Following modern UI standards, this button uses `width='stretch'` to align with the gauge dashboard.
3. Clicking it downloads the report as `ACRAS_Report_{company_id}_{provider}.pdf`.

> **Note:** If a runtime error occurs during PDF generation, a warning replaces the button. The textual report in the left column remains fully accessible for copy-paste.
