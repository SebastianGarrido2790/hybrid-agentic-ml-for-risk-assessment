# ACRAS — Rules & Guardrails Runbook

**Project:** Hybrid Agentic ML for Risk Assessment (ACRAS)
**Document Type:** Runbook · The Rules
**Version:** 1.1
**Date:** 2026-03-09
**Status:** Active — Authoritative Reference

---

## 1. Purpose & Scope

This runbook is the **single source of truth** for all constraints, prohibitions, coding standards, and operational guardrails governing the ACRAS project. It applies to every human or AI agent contributing to the codebase and must be consulted before any architectural change, new feature implementation, or modification of existing pipelines.

This document does **not** describe how the system works (see `reports/docs/architecture/`) or why decisions were made (see `reports/docs/decisions/`). It describes the **boundaries within which all work must operate**.

---

## 2. Core Philosophy

> **"The Brain (Agent) directs; The Hands (Tools) execute."**

All design decisions in ACRAS flow from this principle. LLM agents are probabilistic interpreters. Deterministic Python tools are the only entities permitted to compute, fetch, or transform data. Any violation of this separation is a **critical architectural defect**.

---

## 3. Python Code Standards

### 3.1 Typing

| Rule | Requirement | Enforcement |
| :--- | :--- | :--- |
| **Type Hints** | 100% coverage on all functions, methods, and class attributes | `pyright` (Standard Mode) |
| **py.typed** | Mandatory marker file in `src/` to signal PEP 561 compliance | Project Skeleton Rule |
| **Pydantic Models** | Every external input (API, tool call, config) must use a `BaseModel` | Code review |
| **No Untyped Dicts** | `dict` must never cross module or agent/tool boundaries | Linter (`ruff`) |

**✅ DO:**
```python
class CreditScoreInput(BaseModel):
    company_id: int = Field(..., gt=0, description="Unique company identifier")
    annual_revenue: float = Field(..., alias="ingresos")
```

**❌ DO NOT:**
```python
def get_score(data: dict): ...   # Naked dict — rejected at review
```

### 3.2 Linting & Formatting

All code must pass the following checks **before any commit**:

```bash
uv run ruff check . --output-format=github   # Pycodestyle, Pyflakes, isort, Pyupgrade
uv run ruff format --check .                  # Formatter check
```

Active `ruff` rule sets (from `pyproject.toml`):

| Code | Ruleset | Notes |
| :--- | :--- | :--- |
| `E`, `W` | pycodestyle | Style and whitespace |
| `F` | Pyflakes | Unused imports, undefined names |
| `I` | isort | Import ordering |
| `UP` | pyupgrade | Modern Python idioms |

`E501` (line length) is exempt — handled by the formatter at 88 characters.

### 3.3 Docstrings

**Google-style docstrings are mandatory** on every public function and class.

```python
def calculate_debt_to_equity(total_liabilities: float, shareholders_equity: float) -> float:
    """Calculate Debt-to-Equity ratio.

    Args:
        total_liabilities: Total financial obligations of the entity.
        shareholders_equity: Net assets owned by shareholders.

    Returns:
        Ratio of total liabilities to equity. Returns 0.0 on zero-equity guard.

    Raises:
        ValueError: If either argument is negative.
    """
```

> **Why this matters:** LLM agents and `ToolNode` rely on docstrings to understand tool capabilities. A poorly documented tool leads to misuse that cannot be debugged in the Python layer.

### 3.4 Dependency Management

| Rule | Requirement |
| :--- | :--- |
| **Runtime** | Always use `uv` — never `pip install` directly |
| **Lockfile** | `uv.lock` must be committed with every dependency change |
| **Project Config** | All metadata, dependencies, and tool config live in `pyproject.toml` |
| **Dev extras** | Testing and linting tools must be declared under `[project.optional-dependencies] dev =` |

---

## 4. Agentic Architecture Guardrails

### 4.1 Strict Separation — Brain vs. Hands

| Allowed for Agents (Brain) | Prohibited for Agents |
| :--- | :--- |
| Reasoning, synthesis, classification | Arithmetic and ratio calculations |
| Language generation and formatting | Raw data fetching from CSV/DB |
| Tool orchestration and routing | ML inference |
| Business interpretation of results | Any direct `exec()` or `eval()` |

**Violation Class: CRITICAL.** If an LLM is performing math or retrieving data without a tool, the system is producing hallucinated outputs.

### 4.2 No Naked Prompts

System prompts are **forbidden** from being hardcoded inline anywhere other than `src/agents/prompts.py`.

| Requirement | Location |
| :--- | :--- |
| All system prompts | `src/agents/prompts.py` |
| Config parameters | `src/agents/config.py` (Pydantic Settings) |
| Business logic thresholds (risk bands) | A deterministic Tool or config file — **never the prompt** |

### 4.3 Structured Output Enforcement

- Agents that feed downstream code (e.g., the PDF generator, the risk score parser) must output structured text with machine-parseable tags.
- The CRO/Orchestrator is **required** to emit the terminal tag `SYSTEM FINAL RISK SCORE: [0–100]` as the last numeric signal in its output.
- The `extract_risk_score()` function in `src/ui/app.py` relies on this convention. Any prompt change that removes this tag will break score parsing.

### 4.4 Tool Design Rules

Every LangChain-compatible agent tool must satisfy all of the following:

- [ ] Has a Pydantic `BaseModel` input schema (validates arguments before execution)
- [ ] Has a Google-style docstring (the agent reads this to decide when to call the tool)
- [ ] Is **deterministic** — identical inputs must always produce identical outputs
- [ ] Guards against division by zero and missing data with descriptive error strings (not exceptions)
- [ ] Is **stateless** — tools must not store or mutate global state

### 4.5 Data Leakage Prevention

The `fetch_company_data` tool in `src/agents/tools/lookup_tool.py` **must always exclude** the `target` and `default_probability` columns from its output. These are the ground-truth labels. Exposing them to the LLM agents would constitute information leakage and invalidate all agent evaluations.

> **If you add new fields to `val.csv`, audit which of them are labels or post-hoc derived fields and explicitly exclude them in the lookup tool.**

### 4.6 Provider Hot-Swapping via Config — Not Code

The LLM provider and model names are controlled exclusively via `src/agents/config.py` and the `.env` file. **No model names, API keys, or provider strings may be hardcoded** anywhere in `src/agents/graph.py`, `src/agents/model_factory.py`, or any other module.

Changing a provider requires:
1. Updating `.env` → `DEFAULT_LLM_PROVIDER=gemini`
2. No code change. No restart of backend services.

---

## 5. MLOps Pipeline Rules

### 5.1 FTI Pipeline Independence

The three pipelines must be independently operable at all times:

| Pipeline | Entry Point | Can run without | Must NOT depend on |
| :--- | :--- | :--- | :--- |
| **Feature** | `dvc repro` stages 1–3 | Training & Inference | Model artifacts |
| **Training** | `dvc repro` stages 4–6 | Running Inference API | Live request data |
| **Inference** | `uvicorn src.app.main:app` | Training code | Raw data or DVC stages |

**❌ PROHIBITED:** Importing `src.pipeline.*` modules directly inside `src.app.*` (inference). Preprocessing logic must be serialized into the `preprocessor.pkl` artifact and loaded, not re-executed.

### 5.2 DVC — Versioned Artifacts

All ML artifacts produced by the pipeline must be tracked by DVC:

| Artifact | DVC Stage | Path |
| :--- | :--- | :--- |
| Validation dataset | `data_ingestion` | `artifacts/data_ingestion/val.csv` |
| Fitted preprocessor | `data_transformation` | `artifacts/data_transformation/preprocessor.pkl` |
| Trained model | `model_trainer` | `artifacts/model_trainer/acras_rf_model.joblib` |

> **Rule:** Running `dvc repro` must reproduce all artifacts from raw data. If it does not, the pipeline is broken.

### 5.3 MLflow Experiment Tracking

Every training run must be logged to MLflow. The following fields are **mandatory** per experiment:

| Field | Example |
| :--- | :--- |
| `n_estimators` | `100` |
| `max_depth` | `None` |
| `random_state` | `42` |
| `roc_auc` | `0.893` |
| `f1_score` | `0.76` |
| `precision` | `0.81` |
| `recall` | `0.72` |
| Model artifact | `acras_rf_model.joblib` |

> **Rule:** `random_state=42` is the project-wide seed. All stochastic operations (train/test splits, model fitting) must use this seed to guarantee reproducibility.

### 5.4 Data Contracts

Raw data entering the Feature Pipeline must pass the schema validation defined in `src/pipeline/stage_02_data_validation.py`. A run that produces a validation failure must **halt and raise an exception** — it must not silently continue with corrupt data.

Input schema requirements (from `PredictionInput` Pydantic model):

| Field | Type | Validation Rule |
| :--- | :--- | :--- |
| `ingresos` / `annual_revenue` | `float` | Required |
| `ebitda` | `float` | Required |
| `activos_totales` / `total_assets` | `float` | Required |
| `pasivos_totales` / `total_liabilities` | `float` | Required |
| `patrimonio` / `total_equity` | `float` | Required |
| `caja` / `cash` | `float` | Required |
| `gastos_intereses` / `interest_expenses` | `float` | Required |
| `cuentas_cobrar` / `accounts_receivable` | `float` | Required |
| `inventario` / `inventory` | `float` | Required |
| `cuentas_pagar` / `accounts_payable` | `float` | Required |
| `sector_risk_score` | `float` | Required |
| `years_operating` | `int` | Required |
| `ratio_mora` / `delinquency_ratio` | `float` | Required |
| `ratio_utilizacion` / `credit_utilization` | `float` | Required |
| `revenue_growth` | `float` | Required |
| `margen_beneficio` / `profit_margin` | `float` | Required |
| `score_buro` / `bureau_score` | `float` | Required |
| `ebitda_margin` | `float` | Required (derived pre-API) |
| `debt_to_equity` | `float` | Required (derived pre-API) |
| `current_ratio` | `float` | Required (derived pre-API) |

---

## 6. API Service Rules

### 6.1 Prediction API (`src/app/main.py`)

The FastAPI service must always:
- Load the model artifact **once on startup** via the `lifespan` async context manager (not per-request).
- Store the model and preprocessor in `app.state`, not as module-level globals mutated at runtime.
- Expose a `/health` endpoint (or the Prometheus `/metrics` endpoint) to enable readiness probing.
- Never import from `src.pipeline.*` — it is an inference-only service.

**Default endpoint:** `POST http://localhost:8000/predict`

### 6.2 API Response Contract

The `PredictionOutput` schema is the **contract** between the ML service and the Data Scientist agent. Any change to it must be reflected in:
1. `src/app/schemas.py` — Pydantic model
2. `src/agents/tools/ml_api_tool.py` — Tool's response parsing logic
3. This runbook (update the table below)

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `prediction` | `int` | `0` = Non-Default, `1` = Default |
| `probability` | `float` | Probability of Default (PD), range `[0.0, 1.0]` |
| `risk_level` | `str` | `"Low"` / `"Medium"` / `"High"` (band applied in API layer) |

### 6.3 Graceful Degradation

The `get_credit_risk_score` tool **must not raise exceptions** to the agent. On connection failure or any API error, it must return a descriptive error string so the Data Scientist agent can continue with a qualitative analysis and an appropriate caveat in its report.

---

## 7. Testing Rules

### 7.1 Testing Pyramid

| Layer | Tool | Scope | Coverage Target |
| :--- | :--- | :--- | :--- |
| **Unit** | `pytest` | Tools, pipeline stages, schemas | 80%+ (Gate: 40% initial) |
| **Integration** | `pytest` | DVC pipeline end-to-end execution | At least 1 full pipeline run per stage |
| **API** | `pytest` (HTTPX TestClient) | FastAPI endpoints (`/predict`, `/health`) | All happy-path + error paths |
| **Agentic Evals** | LLM-as-a-Judge | Agent response quality | Relevance, Tool Usage, Schema Adherence, Business Value |

### 7.2 CI Enforcement

The GitHub Actions CI pipeline enforces the following gates on every push and pull request to `master`. A PR **cannot be merged** if any gate fails:

```
Lint & Format (ruff)  ──►  Unit Tests  ──►  Integration Tests  ──►  API Tests
```

The Docker Build Smoke Test runs on path-filtered changes to `Dockerfile`, `docker-compose.yaml`, `pyproject.toml`, `uv.lock`, or `src/**`.

### 7.3 Unit Test Requirements

All unit tests for Tools and Pipeline stages must use `unittest.mock` to prevent:
- Filesystem I/O (use `mock.patch("pandas.DataFrame.to_csv")`)
- Network calls (`mock.patch("requests.post")`)
- Model loading (`mock.patch("joblib.load")`)

Tests that touch the real filesystem or network are **integration tests** and must be placed under `tests/integration/`.

---

## 8. Containerization Rules

### 8.1 Dockerfile Standards

The `Dockerfile` for the prediction service must:
- Use a specific pinned base image (never `python:latest`)
- Use `uv` for dependency installation (not `pip`)
- Run as a **non-root user** (`USER nonroot`) for security
- Use a multi-stage build to exclude dev dependencies from the production image
- COPY ML artifacts from the `artifacts/` directory (pre-built by DVC)

### 8.2 Artifact Placement for Docker

ML artifacts are **gitignored** and produced by `dvc repro`. They must exist locally before running `docker build`. The CI pipeline creates dummy placeholder files for smoke-testing:

```bash
touch artifacts/model_trainer/acras_rf_model.joblib
touch artifacts/data_transformation/preprocessor.pkl
touch artifacts/data_ingestion/val.csv
```

> **Rule:** Never commit `.joblib`, `.pkl`, or `.csv` artifact files to Git. They are managed exclusively by DVC.

---

## 9. Documentation Rules

### 9.1 Four Pillars — Write Before You Push

All architectural changes, new tools, or pipeline modifications must be documented in the correct pillar **before the PR is merged**:

| Pillar | Pillar | Location |
| :--- | :--- | :--- |
| **The Why** | Decisions & Rationale | `reports/docs/decisions/` |
| **The Map** | Architecture & Structure | `reports/docs/architecture/` |
| **The Rules** | Constraints & Guardrails | `reports/docs/runbooks/` ← *This Document* |
| **The Evals** | Quality & Validation | `reports/docs/evaluations/` |
| **The Workflows** | Implementation & How-To | `reports/docs/workflows/` |

### 9.2 Versioning

All documentation must be under Git version control. The `reports/figures/` directory follows the same policy — generated figures are committed as part of the PR that produced them.

---

## 10. The "Do Not Do This" List

> This is a Hard-Stop reference. Violations of these rules require an explicit architectural decision record (ADR) in `reports/docs/decisions/` before they can be permitted.

| # | Prohibition | Impact if Violated |
| :--- | :--- | :--- |
| **R-01** | ❌ DO NOT ask the LLM to perform arithmetic or data transformation | Hallucinated financial ratios in risk reports |
| **R-02** | ❌ DO NOT hardcode model names, API keys, or provider strings in `graph.py` | Hot-swap capability destroyed; credentials leak in version control |
| **R-03** | ❌ DO NOT embed system prompts inline in agent node functions | Violates No Naked Prompts policy; prompts become invisible to version control auditors |
| **R-04** | ❌ DO NOT couple feature preprocessing logic inside the inference API service | Training-serving skew; pipeline independence destroyed |
| **R-05** | ❌ DO NOT mix Streamlit UI logic with agent orchestration logic | Forces restart of UI to change agent behavior; impossible to unit-test |
| **R-06** | ❌ DO NOT allow agents to run `exec()` or `eval()` generated Python code in production | Remote code execution vulnerability |
| **R-07** | ❌ DO NOT expose `target` or `default_probability` columns to the LLM agents | Data leakage; invalidates all agentic evaluations |
| **R-08** | ❌ DO NOT commit ML artifacts (`.joblib`, `.pkl`, large `.csv`) to Git | Repository bloat; artifacts must live in DVC remote storage |
| **R-09** | ❌ DO NOT accept a `ConnectionError` from the ML API silently — return a descriptive error string | Silent failures cause the Data Scientist agent to hallucinate a PD score |
| **R-10** | ❌ DO NOT push directly to `master` — all changes require a PR and passing CI | Branch protection exists for this reason |
| **R-11** | ❌ DO NOT use `dict` as the bridge between the Agent and a Tool or Pipeline | Type safety is destroyed; Pydantic validation is bypassed |
| **R-12** | ❌ DO NOT install packages with raw `pip` — use `uv add` | Lockfile becomes inconsistent; reproducibility is broken |

---

## 11. Incident Response Quick Reference

| Symptom | Likely Cause | First Action |
| :--- | :--- | :--- |
| Agent reports hallucinated ratio | LLM did math instead of calling tool | Audit `prompts.py` — strengthen "NEVER calculate" instructions |
| All CI checks fail after a dependency PR | Missing system lib (`libcairo2-dev`) | Check if `sudo apt-get install` step exists in all CI jobs |
| Risk score always shows `50.0` | `SYSTEM FINAL RISK SCORE:` tag missing in Orchestrator output | Review `ORCHESTRATOR_SYSTEM_PROMPT` in `prompts.py` |
| `ConnectionRefusedError` from ML tool | FastAPI service not running | Start with `uv run uvicorn src.app.main:app --port 8000 --reload` |
| `OSError: model artifact not found` | DVC artifacts not restored | Run `dvc repro` or `dvc pull` to restore artifacts |
| Streamlit shows wrong model in Active Intelligence badge | `.env` override vs `config.py` default conflict | Pydantic Settings priority: OS Env > `.env` > class default |
| Fallback `-lite` suffix appears on PDF | `gemini-2.5-flash-lite` (Tier 3) was triggered | Check HuggingFace and Gemini API token quotas |
