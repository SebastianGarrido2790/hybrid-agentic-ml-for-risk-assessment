# Project Executive Summary: Agentic Credit Risk Assessment System (ACRAS)

## 1. Project Goals

The primary objective of ACRAS is to transform the traditional, manual credit risk assessment process into an automated, intelligent workflow. By integrating deterministic Machine Learning (ML) models with probabilistic AI Agents, the system aims to:

* **Reduce Turnaround Time (TAT):** Shrink the preliminary analysis window from 24–48 hours to under 5 minutes.
* **Enhance Decision Quality:** Minimize human error and bias by standardizing the interpretation of quantitative risk scores.
* **Operational Scalability:** Enable the handling of high-volume, low-complexity SME (Small to Medium Enterprise) loan applications without proportional increases in headcount.
* **Unified Intelligence:** Synthesize disparate data sources (financial ratios, market sentiment, credit history) into a single, cohesive executive report.

## 2. Architectural Design

The system follows a **Microservices-based Agentic Architecture**, decoupling the "Reasoning Engine" (Agents) from the "Computation Engine" (ML Models).

* **Layer 1: The Interface (Streamlit):** A lightweight, user-friendly dashboard for Risk Managers to input company data and view generated reports.
* **Layer 2: The Orchestrator (LangChain):** A central AI agent acting as the "Brain." It parses user intent, breaks down tasks, and delegates work to specialized sub-agents or tools.
* **Layer 3: The MLOps Backend (FastAPI):** A robust, high-performance API wrapping the trained Machine Learning model. It serves as a deterministic "Tool" that the agents can query for precise risk probabilities.

## 3. Agentic Data Science Workflow

### The Machine Learning Microservice (FastAPI)

    • We need to train an ML model (save a .pkl file using a suitable algorithm for the task).

    • Generate code to wrap this model in a FastAPI application. Transforming it into a tool that we will make available to a specialized agent.

    • Create a specific endpoint (e.g., /predict) that accepts input data (defined via Pydantic), runs the model predict function, and returns a structured score or probability (e.g., Probability of Default).

    • Ensure this API acts as a "Tool" that agents can query fundamentally.

### The Agentic Workflow (LangChain)

Define a LangChain structure with the following specific roles (adaptable to my specific business case, but use the "Credit Risk" logic as a template):

• **Agent 1**: The Data Scientist Agent.

    ◦ Goal: Quantitative analysis.

    ◦ Tools: Must have a custom tool to query the FastAPI endpoint created in Step 1.

    ◦ Task: Receive raw data, query the ML model for a prediction/score, and interpret the numerical result (e.g., convert a probability into a credit rating like AAA/CCC).

• **Agent 2**: The Domain Analyst Agent (e.g., Financial Analyst).

    ◦ Goal: Qualitative and rule-based analysis.

    ◦ Task: Analyze unstructured data (news, text) or calculate specific financial ratios (e.g., EBITDA, margins) from structured data.

• **Agent 3**: The Orchestrator/Head Agent.

    ◦ Goal: Synthesis and Reporting.

    ◦ Task: Delegate work to the previous agents, aggregate their findings, and generate a final, professional executive report (e.g., a PDF report for a Risk Manager).

### The Application Layer (Streamlit)

    • Generate an app.py script using Streamlit.

    • The app should allow a user (e.g., a Risk Manager) to input a target entity (e.g., Company Name/ID).

    • It should trigger the LangChain process and display the final generated report/analysis to the user.

## 4. Project Lifecycle (CRISP-DM + MLOps)

We combine the industry-standard **CRISP-DM** (Cross-Industry Standard Process for Data Mining) for model development with modern **MLOps** for deployment and maintenance.

1. **Business Understanding:** Define risk thresholds and regulatory requirements.
2. **Data Engineering:** Collect and preprocess historical financial data.
3. **Modeling (CRISP-DM):** Train, validate, and serialize the credit risk classifier.
4. **Deployment (MLOps):** Wrap the model in a FastAPI container and expose it as a tool.
5. **Agent Integration:** Configure LangChain agents to utilize the deployed tool.
6. **Monitoring & Feedback:** Track agent decisions and model drift to inform retraining cycles.

## 5. Task List: Agentic Credit Risk Assessment System (ACRAS)

### Phase 1: Environment & Project Foundation
- Initialize project structure (`src/`, `tests/`, `configs/`, `notebooks/`)
- Set up `uv` for lightning-fast dependency management (`pyproject.toml`)
- Configure logging and environment variables (`.env` + `pydantic-settings`)
- Initialize a local Git repository
- Initialize DVC (Data Version Control)

### Phase 2: ML Model Engineering (The "Brawn" - Deterministic Tools)
- Implement Data Ingestion & Splitting (`stage_01_data_ingestion.py`)
- Implement Data Validation (`stage_02_data_validation.py`)
- Implement Data Transformation & Preprocessing (`stage_03_data_transformation.py`)
- Train Baseline Model (Random Forest/XGBoost) with fixed random seeds (`stage_04_model_trainer.py`)
- Evaluate Model & Serialize (`.pkl`) with MLflow tracking (`stage_05_model_evaluation.py`)
- Register Model version in local MLflow registry

### Phase 3: MLOps Backend API (FastAPI)
- Define strict Pydantic Schemas for Input/Output (Data Contracts)
- Create FastAPI application factory with custom exception handlers
- Implement `/predict` endpoint to serve the serialized model
- Implement health check, Prometheus metrics, and logging middleware
- Dockerize the API service for containerized deployment

### Phase 4: Agentic Reasoning Engine (The "Brain" - LangChain)
- Create`agent_tools.py`: Wrap FastAPI `/predict` as a structured LangChain Tool
- Create`financial_analyst_tool.py`: Implement deterministic rule-based financial ratios logic
- Implement `orchestrator.py`: Define the Agent State Graph (LangGraph) and routing logic
- Setup prompts: Design versioned System Prompts for Data Scientist and Analyst personas

### Phase 5: User Interface (Streamlit)
- Design main dashboard layout with sidebar for configuration
- Implement Input Form (Company ID and Financial Data)
- Connect UI to the Orchestrator with real-time status updates
- Render Markdown Executive Report with "Chain of Thought" (CoT) expanders

### Phase 6: Integration & Verification
- Execute End-to-End Test: Streamlit → Agent → FastAPI → ML Model
- Perform "LLM-as-a-Judge" evaluation for agent reasoning accuracy
- Verify latency constraints (<30s for full reasoning cycle)
- Finalize Documentation (README, Architecture Diagram, API Docs, PDF Report)

## 6. Design Requirements & Standards

Adhering to MLOps best practices ensures the system is production-ready and sustainable.

* **Reliability:**
    * **Graceful Degradation:** If the ML service is unreachable, the Agent must report the outage rather than hallucinating a score.
    * **Type Safety:** Strict Pydantic models enforce data contracts between Agents and APIs, preventing invalid inputs.

* **Scalability:**
    * **Async Processing:** The FastAPI backend utilizes asynchronous endpoints to handle multiple concurrent agent requests without blocking.
    * **Statelessness:** The model service is stateless, allowing for horizontal scaling (adding more container instances) under load.

* **Maintainability:**
    * **Modularity:** The ML model (`.pkl`) is decoupled from the API logic. Updating the model requires only a file swap and a service restart, not a code rewrite.
    * **Documentation:** Automatic OpenAPI (Swagger) documentation ensures agents and developers always understand the API contract.

* **Adaptability:**
    * **Tool Abstraction:** New tools (e.g., a "Legal Risk Analyzer") can be added to the Agent's toolkit without altering the core orchestration logic.
    * **Model Agnostic:** The architecture supports swapping the underlying algorithm (e.g., from Random Forest to XGBoost) without affecting the upstream agent workflow.

## 7. Technology Stack

* **Language:** Python 3.10+
* **Orchestration Framework:** LangChain (for Agentic workflows)
* **API Framework:** FastAPI (high-performance, async)
* **User Interface:** Streamlit (rapid data app development)
* **Machine Learning:** Scikit-learn (model training), Pandas (data manipulation)
* **Package Management:** `uv` (fast Python package installer)

## 8. Project Analogy: The "AI Orchestra"

To visualize how the system works, imagine an **Orchestra**:

* **The Orchestrator (Conductor):** This is the **LangChain Agent**. It doesn't play an instrument itself; instead, it reads the sheet music (User Request), sets the tempo, and cues specific musicians when needed.
* **The Musicians (Tools):**
    * The **Violinist** is the **ML Model (FastAPI)**. It is highly specialized, practiced, and deterministic—it plays the exact notes (Risk Score) it was trained to play.
    * The **Percussionist** is the **Financial Analyst Tool**. It adds texture and rhythm (Qualitative Context) to the piece.
* **The Audience:** The **Risk Manager**. They don't need to know how to play the violin or read the score; they simply enjoy the cohesive, finished performance (The Executive Report).
