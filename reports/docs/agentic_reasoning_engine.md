# Agentic Reasoning Engine Report

## 1. Overview
The **Agentic Reasoning Engine** serves as the "Brain" of the ACRAS system. It utilizes **LangChain** and **LangGraph** to orchestrate a sophisticated workflow where a Probabilistic Agent (LLM) delegates specific tasks to Deterministic Tools (ML Models, Calculators) to produce a high-confidence credit risk assessment.

## 2. Architecture

### 2.1 The Hybrid Model Strategy
To balance performance, cost, and privacy, the system employs a configurable **Hybrid LLM** approach:
*   **Google Gemini (Cloud):** The primary model for complex reasoning and synthesis.
*   **Hugging Face (Local/Inference):** A fallback or privacy-centric option using open-source models like Llama 3.
    
    We using `meta-llama/Meta-Llama-3-8B-Instruct` as the Hugging Face model. This model is available at Hugging Face Inference API (https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct).

This logic is encapsulated in `src/agents/model_factory.py`.

### 2.2 The State Graph (LangGraph)
The workflow is defined as a State Graph (`src/agents/graph.py`) with the following nodes:
1.  **Agent Node:** The LLM receives the state (messages) and decides whether to call a tool or providing a final answer.
2.  **Tools Node:** Executes the requested tool (e.g., query the ML API, calculate a ratio) and returns the output to the Agent.

### 2.3 Tools as Microservices
To prevent "hallucinations" in critical areas, we wrap external systems and math in typed tools:
*   **`get_credit_risk_score` (`ml_api_tool.py`):**
    *   **Purpose:** Wraps the FastAPI `/predict` endpoint.
    *   **Safety:** Uses a shared Pydantic schema to ensure the Agent provides all 20 required features. Returns natural language error messages if the API is down.
*   **Financial Ratios (`finance_tool.py`):**
    *   **Purpose:** Deterministic Python functions for calculations (e.g., Debt-to-Equity).
    *   **Safety:** Prevents the LLM from doing arithmetic, which is a known weak point of language models.

### 2.4 Workflow Diagram
The following diagram illustrates the granular interaction flow between the user, the agent, and the deterministic tools:

```mermaid
graph TD
    User([User Request]) --> Factory[Model Factory]
    Factory --> LLM[LLM Instance: Gemini/HF]
    LLM --> Graph{LangGraph Orchestrator}
    
    subgraph Iterative Loop
        Graph --> Agent[Agent Node: Reason]
        Agent --> Decision{Action?}
        Decision -- Tool Call --> Tools[Tools Node: Execute]
        Tools --> Observation[Tool Observation]
        Observation --> Agent
    end
    
    Decision -- Final Answer --> Synthesis[Synthesize Report]
    Synthesis --> Output([Markdown Risk Assessment])
    
    subgraph Deterministic Tools
        Tools --- ML_API[ML API: get_credit_risk_score]
        Tools --- Math[Math: finance_tool]
    end
```

## 3. Configuration & Security
*   **Settings:** Managed via `src/agents/config.py` using `pydantic-settings`.
*   **Secrets:** API Keys (`GOOGLE_API_KEY`, `HUGGINGFACEHUB_API_TOKEN`) are loaded exclusively from `.env` and never hardcoded.

## 4. Testing & Validation
The agentic layer is tested in `tests/unit/test_agent_tools.py` using `pytest`.
*   **Mocking:** We use `unittest.mock` to simulate the FastAPI response, allowing us to test the Agent's tool logic without needing the actual API server running.
*   **Scenarios:**
    *   **Success:** Valid inputs yield a formatted string with Risk Level and Probability.
    *   **Failure:** Connection errors or invalid inputs are caught and handled gracefully.

## 5. How to Run the Agent

Currently, the agent is orchestrated as a compiled graph. To run the agent in a development environment:

1.  **Environment Setup:** Ensure your `.env` file has a valid `GOOGLE_API_KEY`.
2.  **API Status:** Ensure the ML Model API (FastAPI) is running at `http://localhost:8000`.
3.  **Python Script:** Use the following integration snippet (planned for Phase 5 frontend):

```python
from src.agents.graph import app
from langchain_core.messages import HumanMessage

# Initial State
inputs = {"messages": [HumanMessage(content="Assess the risk for a company with 1M revenue and 200k EBITDA.")]}

# Run the Graph
for output in app.stream(inputs):
    for key, value in output.items():
        print(f"Output from node '{key}':")
        print(value)
```

## 6. Future Roadmap
*   **Integration Tests:** Verify the full `Agent -> Tool -> API` loop in a live environment.
*   **Evaluations:** Implement "LLM-as-a-Judge" using DeepEval to score the quality and faithfulness of the Agent's final reports.

