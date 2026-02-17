### User Story & Problem Framing

**Project:** Agentic Credit Risk Assessment System (ACRAS)

---

### 1. Problem Framing

**The "Why" behind the automation.**

**The Current State (The "Toil"):**
In modern banking, a Senior Credit Risk Manager spends approximately 70% of their workday on data aggregation and only 30% on actual risk assessment. To evaluate a single corporate loan application, they must manually:

1. Extract financial ratios from PDF statements.
2. Query internal databases for credit history.
3. Search external news sources for reputational risk (adverse media).
4. Manually input these figures into a rigid scoring model.

**The Friction Point:**
This manual workflow results in a **Turnaround Time (TAT) of 24 to 48 hours** per application. It creates a bottleneck where high-value decisions are delayed by low-value data gathering. Furthermore, dependence on purely manual review or opaque, closed-source automated tools can lead to high costs and lack of auditability.

**The Opportunity (McKinsey Alignment):**
By deploying an **Agentic AI Workflow** using **Hybrid Models (Gemini + Open Source)**, we can invert this ratio. The AI Agents handle the deterministic scoring (ML) and the qualitative synthesis (NLP) using the most cost-effective model for the task, presenting the manager with a "Decision-Ready" report. This shifts the manager's role from "Data Gatherer" to "Strategic Decision Maker," reducing TAT from days to minutes while maintaining full data control.

---

### 2. The Core User Story

**As a** Senior Credit Risk Manager,
**I want to** input a target company’s identifier into a unified dashboard and immediately receive a synthesized "Credit Risk Executive Report,"
**So that** I can review the machine-generated risk score alongside qualitative context (market sentiment/ratios) and make a final approval or rejection decision in under 5 minutes.

---

### 3. Acceptance Criteria (Definition of Done)

*The story is considered complete when the following conditions are met:*

* **Input Validated:** The Streamlit interface accepts a Company ID and successfully passes it to the Agent Orchestrator.
* **Agent Routing:** The Orchestrator correctly identifies the need for quantitative data and autonomously triggers the `get_credit_risk_score` tool (FastAPI).
*   **Data Integrity:** The Risk Score displayed in the final report matches the exact output of the ML model (no LLM hallucination of the numbers).
*   **Qualitative Context:** The report includes at least one paragraph of text analysis derived from the `analyze_financial_ratios` tool.
*   **Model Auditability:** The report metadata indicates which model (e.g., Gemini 1.5 vs. Llama 3) was used to generate the qualitative analysis.
*   **Output Format:** The final output is rendered in the UI as a clean, structured Markdown report.

---

### 4. Contextual Scenario (A Day in the Life)

* **Trigger:** The bank receives an urgent loan application from "TechStart Solutions Inc."
* **Action:** The Risk Manager, Sarah, opens the ACRAS Dashboard. She types "TechStart Solutions" and clicks "Generate Report."
* **System Behavior:**
* *The "Brain" (Orchestrator)* wakes up.
* *Agent A (Data Scientist)* grabs the financials, hits the ML API, and reports: "Probability of Default is 18% (Low Risk)."
* *Agent B (Analyst)* scans the context and reports: "Cash flow is strong, but sector volatility is high."
* *The "Brain"* combines these: "Recommend Approval, but monitor sector volatility."


* **Outcome:** Sarah reads the 1-page summary. She sees the low default probability backed by strong cash flow. She hits "Approve." Total time elapsed: 45 seconds.
