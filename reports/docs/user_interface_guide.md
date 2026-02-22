# ACRAS User Interface Guide

## 1. Introduction
The **ACRAS User Interface** is a Streamlit-based web application designed for Risk Managers. It provides a clean, interactive dashboard to input company financial data, trigger the AI analysis, and visualize the risk assessment results.

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

## 3. Using the Interface
1.  **Select Company ID:** Use the dropdown in the sidebar to select a valid company for assessment.
2.  **View Context:** The sidebar displays quick references like annual revenue.
3.  **Initiate Assessment:** Click the **Initiate** button to trigger the **Agent Cluster**.
4.  **Reset:** Use the **Reset** button to clear the current results and start a fresh session.
5.  **Monitor Cluster Sync:**
    *   **Financial Analyst:** Extracts data and performs deterministic ratio calculations.
    *   **Data Scientist:** Interprets ML predictions and quantitative metrics.
    *   **Director (CRO):** Orchestrates the findings into the final executive report.
6.  **Analytics Dashboard:**
    *   **Gauge Chart:** Interactive visualization of the risk score (0-100).
    *   **Decision Logic Box:** Instant classification (Approve, Review, Reject).
7.  **Download Executive PDF:** A one-click button to generate a professionally formatted PDF report for offline storage. 

## 4. Understanding the Agent Cluster Workflow

The system uses three specialized AI agents to ensure depth and precision:

### 4.1 Financial Analyst (The "Auditor")
*   **Role:** Performs deep-dives into core financials.
*   **Tools:** `fetch_company_data`, `calculate_debt_to_equity`, `calculate_ebitda_margin`, `calculate_current_ratio`.
*   **Output:** Formatted summaries of Liquidity, Solvency, and Profitability.

### 4.2 Data Scientist (The "Modeler")
*   **Role:** Translates financial profiles into ML-driven risk scores.
*   **Tools:** `get_credit_risk_score`.
*   **Output:** Predictive analysis and interpretation of the Model PD (Probability of Default).

### 4.3 Chief Risk Officer (The "Director")
*   **Role:** Chief synthesizer and final decision-maker.
*   **Output:** The final executive report with mandatory structural layout.

## 5. Resilience: The 3-Tier Fallback Mechanism
ACRAS is built for 100% reliability using a **Multi-Tier Fallback** system:
- **Tier 1 (Primary):** The default model (Gemini or Hugging Face Qwen 72B). 
- **Tier 2 (Fallback):** If the primary fails, the system automatically swaps to the alternative provider’s high-performance model. 
- **Tier 3 (Reliable):** A high-uptime, low-latency model (Gemini Flash Lite) acts as the final safety net.
- **Observability:** You can monitor the real-time "Tier Swaps" directly in the application logs and terminal.

## 6. Understanding the Inputs

### 6.1 Primary Financials (USD)
These are the core metrics used to gauge the company's size and profitability.
*   **Annual Revenue:** The total amount of money brought in by a company's operations. High revenue indicates market presence.
*   **EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization):** A measure of a company's overall financial performance and is used as an alternative to net income in some circumstances. Ideally, this should be positive.
*   **Net Profit:** The actual profit after working expenses not included in the calculation of gross profit have been paid.
*   **Total Assets:** The sum of all current and non-current assets owned by the company.
*   **Total Liabilities:** The sum of all debts and obligations owed by the company.
*   **Total Equity:** The value of the shares issued by a company (Assets - Liabilities).

### 6.2 Detailed Financials & Ratios
These inputs refine the risk model by providing data on liquidity and operational efficiency.
*   **Cash on Hand:** Immediate liquid assets available for use. Crucial for short-term solvency.
*   **Interest Expenses:** The cost incurred by an entity for borrowed funds. High interest expenses relative to EBITDA serve as a warning sign.
*   **Accounts Receivable:** Money owed to a company by its debtors.
*   **Inventory Value:** The current value of raw materials, work-in-progress, and finished goods.
*   **Accounts Payable:** Money owed by a company to its creditors.
*   **Sector Risk Score (0-10):** A subjective or external rating of the risk inherent to the company's industry (10 = High Risk).
*   **Years Operating:** How long the company has been in business. Longer usually implies stability.
*   **Delinquency Ratio (0-1):** The percentage of past payments that were late or missed. A critical risk indicator.
*   **Credit Utilization (0-1):** The ratio of current credit being used to the total credit limit available. Lower is generally better.
*   **Revenue Growth Rate:** The percentage increase (or decrease) in revenue over a specific period.
*   **Bureau Score (300-850):** A standardized credit score from an external bureau (e.g., FICO).
*   **Profit Margin:** Net Profit / Revenue. Indicates how much of every dollar of sales a company keeps in earnings.

### 6.3 Market Conditions
The external economic environment can significantly impact credit risk.
*   **Stable:** Normal economic conditions with predictable growth.
*   **Volatile:** Unpredictable market swings, requiring caution.
*   **Recession:** Economic downturn; generally increases the probability of default across the board.
