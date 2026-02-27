# ACRAS User Interface Guide

## 1. Introduction
The **ACRAS User Interface** is a Streamlit-based web application designed for Risk Managers. It provides a clean, interactive dashboard to input company financial data, trigger a multi-agent AI analysis, and visualize the risk assessment results in real-time.

## 2. How to Run the App
To launch the application locally, follow these steps:

1.  **Start the ML API Backend:**
    Open a terminal and run the FastAPI server (which hosts the credit scoring model):
    ```bash
    uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

2.  **Start the Streamlit Frontend:**
    Open a *new* terminal window and run the Streamlit app:
    ```bash
    uv run streamlit run src/ui/app.py
    ```

3.  **Access the Dashboard:**
    Open your browser and navigate to `http://localhost:8501`.

### 2.1 Launching the App with a Single Command
To simplify the launch process, you can use the provided batch script `launch_acras.bat`. This script automates the entire startup sequence:

1.  **Run the script:**
    ```bash
    .\launch_acras.bat
    ```
2.  **Monitor the process:**

    The script will automatically:
    *   Sync dependencies using `uv sync` to ensure your environment is exactly as defined in `pyproject.toml`.
    *   Launch the FastAPI backend in a minimized window (so it doesn't clutter your desktop but remains active).
    *   Wait for 5 seconds for the API to initialize to warm up before the UI connects.
    *   Launch the Streamlit frontend in the foreground (your main window).

## 3. Global Hot-Swapping (Modern Workflow)
The ACRAS UI is designed for live iteration. You can change the **LLM Provider** or individual **Models** in the `src/agents/config.py` file without ever restarting the Streamlit application.
1.  **Edit Config:** Change a model name or provider in the code.
2.  **Immediate Sync:** The "Active Intelligence" badge in the UI header will update instantly.
3.  **Initiate:** Click "Initiate" to run the agents with the new configuration immediately.

## 4. Key Interface Components

### 4.1 The Header Badge (Observability)
Located at the top right, the **Active Intelligence Badge** displays:
*   **Provider:** (e.g., GEMINI or HUGGINGFACE)
*   **Active Model:** The specific architecture currently driving the primary orchestration logic.

### 4.2 Control Panel (Left Sidebar)
*   **Target Entity ID:** Dropdown to select a company from the processed database.
*   **Key Metrics:** Instant preview of Revenue, EBITDA, and Bureau Score for the selected entity.
*   **Engine Controls:**
    *   **Initiate:** Triggers the synchronous multi-agent cluster.
    *   **Reset:** Clears the session state and resets the dashboard.

### 4.3 Agent Cluster Synchronization Logs (Center)
This section provides a deep look "under the hood" of the AI's reasoning:
*   **Status Indicators:** Real-time messages showing which agent is active and which tool is being called.
*   **Resilience Tracking:** If a model fails, you will see explicit fallback logs:
    *   `🔄 Falling back to 1st Fallback (gemini-1.5-flash)...`
    *   `⚠️ Primary (Qwen) failed.`
*   **Agent Logs:** Detailed expanders for the **Analyst**, **Scientist**, and **Director** showing their individual qualitative and quantitative findings.

### 4.4 Analytics Dashboard (Right)
*   **Risk Gauge:** A Plotly-powered visualization of the final Risk Score (0-100).
*   **Decision Logic:** Color-coded classification (Approve, Review, Reject) based on the final risk intensity.

## 5. The Agent Cluster Workflow

| Agent | Focus | Key Deliverables |
| --- | --- | --- |
| **Financial Analyst** | Financial Health | Liquidity/Solvency metrics, key ratio tables, and risk ratings per metric. |
| **Risk Data Scientist** | ML Prediction | Probability of Default (PD), interpretation of the ML engine's features, and quantitative tiering. |
| **Director (CRO)** | Executive Synthesis | Final executive report, 6-metric KPI dashboard, and the final "Approve/Reject" directive. |

## 6. Resilience: 3-Tier Fallback Mechanism
ACRAS ensures consistency using a tiered system that is visible in the UI logs:
1.  **Primary:** Your preferred high-performance model (e.g., Qwen2.5-7B or Gemini).
2.  **Fallback 1:** Cross-provider switch to ensure uptime if one ecosystem is down.
3.  **Fallback 2:** Standardized `gemini-2.5-flash-lite` for high availability and low latency.

## 7. Downloading Reports
Once the assessment is complete, use the **"Download Executive PDF"** button (centered at the bottom) to generate a professional PDF including the full executive summary and the KPI dashboard for official documentation.
