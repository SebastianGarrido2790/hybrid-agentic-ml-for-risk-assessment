# ACRAS: Advanced Agentic Credit Risk & Analysis System

![Version](https://img.shields.io/badge/Version-1.1--In--Development-blueviolet)
![Tech Stack](https://img.shields.io/badge/Stack-Python_|_FastAPI_|_Streamlit_|_LangGraph-blue)
![License](https://img.shields.io/badge/License-Proprietary-red)

**ACRAS** is a hybrid Agentic MLOps framework designed to transform corporate credit risk assessment. It moves beyond static scoring by orchestrating a cluster of specialized AI agents that collaborate with deterministic Machine Learning models to produce deep, qualitative, and quantitative risk narratives.

> [!NOTE]
> **Project Status:** This repository is currently under active development. Core reasoning engines and UI synchronization are functional, with advanced evaluation frameworks and integration tests in the pipeline.

---

## 🧠 The Agentic Brain (Antigravity Architecture)

ACRAS uses a multi-agent cluster orchestrated via **LangGraph**, following the "Brain vs. Brawn" principle: agents handle reasoning, while deterministic tools handle the heavy lifting.

### 1. The Agent Cluster
*   **📊 Financial Analyst**: Auditor-style agent that extracts metrics and performs deterministic ratio calculations (Liquidity/Solvency).
*   **🔬 Risk Data Scientist**: Translates financial profiles into ML-driven risk scores, interpreting the Probability of Default (PD).
*   **👔 Chief Risk Officer (Director)**: Final synthesizer that compiles findings into an executive-grade directive.

### 2. Resilience: 3-Tier Fallback Engine
To ensure 100% reliability in production, ACRAS implements a self-healing fallback mechanism:
1.  **Primary**: Your preferred model (e.g., Qwen2.5-7B or Gemini 1.5 Pro).
2.  **1st Fallback**: Automatic cross-provider switch (e.g., if HF is down, it swaps to Google Gemini).
3.  **2nd Fallback**: Final safety net using standardized high-availability models (`gemini-1.5-flash`).

---

## ⚡ Key Features

*   **Global Hot-Swapping**: Update LLM providers or model names in `config.py` and see them refresh instantly in the active app without restarts.
*   **UI Observability**: A real-time "Active Intelligence" badge and cluster synchronization logs let you watch the AI's "Chain of Thought" and tool execution.
*   **Deterministic Integrity**: Critical calculations and ML predictions are wrapped in Pydantic-validated tools to prevent LLM hallucinations.
*   **Executive Reporting**: One-click generation of professional PDF reports including KPI dashboards and qualitative insights.

---

## 🚀 Quick Start

### 1. Prerequisites
*   Python 3.10+
*   [uv](https://github.com/astral-sh/uv) (Recommended for lightning-fast dependency management)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/SebastianGarrido2790/hybrid-agentic-ml-for-risk-assessment.git
cd hybrid-agentic-ml-for-risk-assessment

# Sync dependencies
uv sync
```

### 3. Launching the System
Use the provided batch script to launch the API and UI simultaneously:
```bash
.\launch_acras.bat
```

---

## 🛠️ Configuration (The Command Center)

ACRAS uses a dual-layer configuration system managed via `src/agents/config.py`.

*   **Dynamic Source**: Edit `src/agents/config.py` for live hot-swapping.
*   **Environment**: Store secrets (`GOOGLE_API_KEY`, `HUGGINGFACEHUB_API_TOKEN`) in a `.env` file.

```env
# Example .env
GOOGLE_API_KEY=your_key_here
HUGGINGFACEHUB_API_TOKEN=your_token_here
```

---

## 📈 Roadmap & Upcoming Features
- [x] Multi-agent cluster orchestration (LangGraph)
- [x] Dynamic model hot-swapping
- [x] Real-time UI observability logs
- [ ] **Phase 6**: LLM-as-a-Judge evaluation framework (DeepEval)
- [ ] **Phase 7**: Full CI/CD integration for automated model retraining
- [ ] **Phase 8**: Interactive "Agentic Healing" for data correction

---

*Developed by **Sebastian Garrido** - Exploring the intersection of Agentic AI and MLOps.*
