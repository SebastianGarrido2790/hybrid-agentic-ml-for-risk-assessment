# Product Requirements Document (PRD)

This Product Requirements Document (PRD) is structured to reflect professional industry standards, serving as a blueprint for the "Agentic Credit Risk Assessment System" (ACRAS). It bridges the gap between business objectives (McKinsey use case) and technical implementation (MLOps + Agentic workflows).

---

**Project Name:** Agentic Credit Risk Assessment System (ACRAS)

**Version:** 1.0

**Status:** Draft / Planning

**Document Owner:** Lead AI Engineer

**Date:** February 10, 2026

---

## 1. Executive Summary

**Background:** Current credit risk assessment processes in banking are manual, fragmented, and time-intensive. Risk Managers spend approximately 70% of their time gathering data from disparate sources (financial statements, news, credit bureaus) and only 30% on actual decision-making. This results in high Turnaround Time (TAT) (24–48 hours) and potential human error in data synthesis.

**Product Vision:** To build an automated, hybrid AI system where autonomous agents collaborate to execute the "heavy lifting" of data collection and initial analysis. By wrapping a deterministic Machine Learning model (Random Forest/XGBoost) as a tool for a probabilistic reasoning agent (**Gemini / Open Source LLM**), we aim to reduce the preliminary assessment time from days to minutes.

**Business Value (McKinsey Alignment):**

*   **Operational Efficiency:** Reduce manual data entry and calculation time by ~90%.
*   **Consistency:** Standardize the interpretation of quantitative risk scores across the organization.
*   **Agility:** Enable real-time risk reporting for SME (Small to Medium Enterprise) accounts.
*   **Auditability & Vendor Independence:** Leverage Open Source models to ensure full control over data privacy and avoid vendor lock-in.

---

## 2. User Personas

| Persona | Role | Pain Points | Goals |
| --- | --- | --- | --- |
| **The Risk Manager** (Primary) | Final decision maker on credit applications. | Overwhelmed by raw data; fatigue from repetitive calculation tasks. | Wants a synthesized, "ready-to-review" executive summary to make faster approvals/rejections. |
| **The MLOps Engineer** (Secondary) | Maintainer of the model and infrastructure. | Hard to debug "black box" LLM decisions; managing model drift. | Needs clear logging, versioned models, and a decoupled architecture where the ML model can be updated without breaking the agent. |

---

## 3. Functional Requirements

The system is divided into three functional layers: The Interface, The Agentic Orchestrator, and The MLOps Backend.

### 3.1 The Application Layer (Streamlit)

* **FR-01 (Input):** The interface must allow the user to input a unique Company Identifier (Name or ID) and, optionally, override specific financial parameters (simulating "what-if" scenarios).
* **FR-02 (Trigger):** A single "Generate Report" action must initiate the backend agentic workflow.
* **FR-03 (Output):** The interface must render the final response in a structured Markdown format, separated into: Executive Summary, Quantitative Score, Qualitative Insights, and Final Recommendation.

### 3.2 The Agentic Workflow (LangChain)

* **FR-04 (Orchestrator Agent):** A central "Head Agent" must allow for task delegation. It must break down the user request into two sub-tasks: *Quantitative Analysis* and *Qualitative Analysis*.
* **FR-05 (Data Scientist Tool):** A specific tool must exist that allows the agent to construct a JSON payload and query the ML Microservice. It must handle API errors (e.g., 500 or 404) gracefully.
* **FR-06 (Financial Analyst Tool):** A tool must exist for rule-based logic (e.g., calculating EBITDA margins from raw inputs) or qualitative context retrieval (simulated news/market sentiment).
* **FR-07 (Synthesis):** The Orchestrator must combine the deterministic output (Risk Score: 0.82) with the probabilistic context (Sentiment: Positive) to form a nuanced conclusion.

### 3.3 The Machine Learning Microservice (FastAPI)

* **FR-08 (Inference Endpoint):** A RESTful endpoint (`POST /predict`) must accept strict Pydantic-validated JSON input.
* **FR-09 (Model Versioning):** The API must load a pre-trained `.pkl` model at startup.
* **FR-10 (Response Schema):** The API must return both the raw probability (float) and the mapped risk label (Low/Medium/High) to reduce ambiguity for the agent.

---

## 4. Non-Functional Requirements (NFRs)

* **NFR-01 (Latency):** The end-to-end process (User Click → Final Report) should take no longer than 30 seconds.
* **NFR-02 (Reliability):** The ML Microservice must have 99.9% uptime. If the ML service is down, the Agent must report "Unable to calculate quantitative score" rather than hallucinating a number.
* **NFR-03 (Modularity):** The ML model file must be replaceable without modifying the Agent's code.
*   **NFR-04 (Traceability):** All agent decisions (intermediate tool calls) must be logged to the UI or console for "Chain of Thought" auditing.
*   **NFR-05 (Auditability):** The system must explicitly log which model (Gemini Cloud vs. Local OS Model) was used for each reasoning step.

---

## 5. Technical Architecture & Stack

*   **Frontend:** Streamlit (Python).
*   **Orchestration:** LangChain / LangGraph.
*   **LLM Provider:** **Google Gemini** (Cloud) & **Hugging Face** (Local Open Source).
*   **Backend API:** FastAPI (Uvicorn server).
* **Model serialization:** Pickle (`.pkl`).
* **Environment Management:** `uv` or `venv`.

### Data Flow Diagram

`[User Input]` -> `[Streamlit App]` -> `[Orchestrator Agent]`
|
+---> `[Tool: Data Scientist]` -> `(HTTP Request)` -> `[FastAPI /predict]` -> `[ML Model]`
|
+---> `[Tool: Financial Analyst]` -> `(Internal Logic)` -> `[Ratio Calculation]`
|
`[Orchestrator synthesizes results]` -> `[Final PDF/Text Report]` -> `[Streamlit UI]`

---

## 6. Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation Strategy |
| --- | --- | --- | --- |
| **Model Hallucination:** Agent invents financial data when calling the API. | Medium | High | Use strictly typed Pydantic models for Tool definitions. Enforce "Don't guess" system prompts. |
| **API Failure:** The connection between Agent and FastAPI drops. | Low | High | Implement retry logic in LangChain; return graceful error messages to the user. |
| **Black Box Logic:** User doesn't trust the score. | High | Medium | The UI must display the *Chain of Thought* (verbose mode) so the user sees *why* the decision was made. |

---

## 7. Success Metrics (KPIs)

1. **System Success Rate:** % of requests that result in a successfully generated report without error.
2. **Tool Utilization Accuracy:** % of times the Orchestrator correctly calls the "Data Scientist" tool for numerical questions vs. the "Analyst" tool for text questions.
3. **User Latency:** Average time to generate a report.
