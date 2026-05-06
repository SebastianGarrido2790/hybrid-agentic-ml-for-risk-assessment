# ACRAS Codebase Review — Production Readiness & Portfolio Assessment

**Date:** 2026-05-06
**Version:** 2.0 (Production-Elite Audit)
**Scope:** Full codebase — 54 Python source files, 17 test files, 3 CI workflows, 3 YAML configs, Dockerfile, docker-compose, `pyproject.toml`, and 28+ documentation files.

---

## Overall Verdict

ACRAS is a **production-grade reference architecture** that successfully demonstrates the core philosophy: *"The Brain (Agent) directs; The Hands (Tools) execute."* The system implements a 3-agent LangGraph relay with deterministic guardrails, a 7-stage DVC pipeline, a containerized FastAPI inference microservice, and MLflow experiment tracking — all orchestrated through a modular, typed Python codebase.

**Since v1.1**, the project has resolved all Critical blockers (credential exposure, type-safety gaps, missing test coverage). What remains are **"Elite" maturity enhancements** — the difference between a strong production system and an industry-reference architecture.

**v2.0 Update (Hardening Complete):** The "Operational Hardening" phase (Sprint 1) is now 100% complete. All `print()` statements have been migrated to a structured logging stack, magic numbers have been extracted to a centralized configuration layer, and the API boundary has been hardened with a global exception handler and sanitized error responses. Performance bottlenecks in tool data loading have been resolved via memoization.

**Maturity Level: Production-Ready (8.4/10) → Target: Elite Reference (9.2/10)**

---

## 1. Strengths ✅

### 1.1 Architecture & Design (Rules 1.2, 1.3, 1.8)

| Strength | Evidence | Rule |
|:---|:---|:---|
| **FTI Pattern** | 7-stage DVC pipeline with explicit artifact handoffs across Augmentation → Ingestion → Validation → Transformation → Training → Evaluation → Registration | 2.14 |
| **Brain vs. Brawn** | Agents reason via LangGraph (`graph.py`); tools handle deterministic math (`finance_tool.py`) and API calls (`ml_api_tool.py`) via Pydantic-validated inputs | 1.2 |
| **Sequential Agent Pattern** | "Relay Team" — Financial Analyst → Data Scientist → CRO Orchestrator with structured state handoff via `AgentState(TypedDict)` | 1.8.2 |
| **Deterministic Guardrails** | `orchestrator_node()` injects regex-extracted mora/liquidity thresholds as a `SYSTEM RISK ADVISORY` block — LLM cannot override deterministic facts | 1.4 |
| **Config Separation** | Three-tier YAML (`config.yaml` paths, `params.yaml` hyperparams, `schema.yaml` data contracts) | 2.3 |
| **Typed Entities** | Frozen `@dataclass` in `config_entity.py` enforce immutability across all 7 pipeline stages | 2.3 |

### 1.2 Agentic Layer (Rules 1.5, 1.7, 1.8)

| Strength | Evidence | Rule |
|:---|:---|:---|
| **3-Tier Fallback** | `invoke_with_fallback()` cascades Primary → Cross-provider → Lite with full logging per tier | 1.8.3 |
| **Hot-Swapping** | `importlib.reload()` enables runtime model/config changes without restart | 1.8.1 |
| **Tool Validation** | Finance tools use Pydantic `args_schema`; division-by-zero handled explicitly | 1.3 |
| **Provider Factory** | `model_factory.py` abstracts Gemini/HuggingFace behind `get_llm()` (Strategy Pattern) | 1.8.1 |
| **Gemini Normalization** | `invoke_with_fallback()` normalizes `list[dict]` content to plain strings — prevents downstream concatenation failures | 1.4 |
| **Centralized Prompts** | All system prompts in `src/agents/prompts.py`, separated from execution logic | 1.5 |

### 1.3 MLOps & CI/CD (Rules 2.14, 6.1, 6.2)

| Strength | Evidence | Rule |
|:---|:---|:---|
| **DVC Pipeline** | Full DAG with `deps`, `params`, `outs`, `metrics` — reproducible and cacheable | 2.14 |
| **MLflow Integration** | Experiment tracking, metric logging, model registry with ROC-AUC gating | 2.14.4 |
| **Environment-Aware Config** | `mlflow_config.py` resolves URIs across local/docker/production | 6.1 |
| **CI Pipeline** | Lint-gated parallel test suites (unit, integration, API) + type-check job | 6.2 |
| **Multi-stage Dockerfile** | `uv` builder → slim runtime, non-root `appuser`, health check, layer caching | 6.1 |
| **Dependabot** | Automated dependency updates for pip and GitHub Actions | 6.2 |

### 1.4 Testing (Rule 4.1)

| Strength | Evidence | Rule |
|:---|:---|:---|
| **Test Pyramid** | 15 unit tests + 1 integration + 1 API test suite | 4.1.1 |
| **Mock Strategy** | `conftest.py` provides lifespan-mocked `TestClient` with `app.state` fixtures | 4.1.2 |
| **Edge Cases** | API tests cover Low/Medium/High risk, validation errors, and service unavailability | 4.1.1 |
| **Coverage Gate** | `--cov-fail-under=40` enforced in CI | 4.1.3 |

### 1.5 Documentation (Rule 5.1)

| Strength | Evidence | Rule |
|:---|:---|:---|
| **Five Pillars** | Reports follow `architecture/`, `decisions/`, `evaluations/`, `references/`, `runbooks/`, `workflows/` | 5.1 |
| **Module Docstrings** | Every Python file has a module-level docstring | 2.1 |
| **Google-style Docstrings** | Functions document args, returns, raises — consistent throughout | 2.1 |

---

## 2. Resolved Gaps ✅ (v1.1 → v2.0)

| # | Gap | Status | Resolution |
|:--|:---|:---:|:---|
| 2.1 | Hardcoded API keys in `.env` | ✅ | `.env.example` added, keys gitignored, rotation guidance documented |
| 2.2 | No `pyright` config/enforcement | ✅ | `[tool.pyright]` in `pyproject.toml`, CI type-check job, `py.typed` marker |
| 2.3 | Test coverage gaps (5 components untested) | ✅ | 5 new test modules + `pytest-cov` CI gate |
| 2.9 | `pydantic-settings` not in deps | ✅ | Added to `pyproject.toml` |
| 2.10 | Missing `__init__.py` files | ✅ | Propagated throughout `src/` and `tests/` |
| 2.11 | CI missing type-check and coverage gates | ✅ | Both integrated as parallel CI jobs |
| 3.8 | No `py.typed` marker | ✅ | Added to `src/` root |

---

## 3. Open Gaps — Tier 1: Operational Hardening 🔴

These gaps affect production reliability and must be addressed before any external deployment.

### 3.1 ~~`print()` Statements in Production Code (Rule 4.2)~~ ✅ ADDRESSED (v2.0)

~~`print()` bypasses the configured `RotatingFileHandler` and `RichHandler` logging stack, producing unstructured output that is invisible to any log aggregation system.~~

| File | Line | Current | Required |
|:---|:---|:---|:---|
| `graph.py` | L199 | `print(f"🤖 {agent_name}...")` | `logger.info(...)` |
| `graph.py` | L212 | `print(f"! {agent_name}...")` | `logger.warning(...)` |
| `endpoints.py` | L69 | `print(f"Prediction Error: ...")` | `logger.error(...)` |
| `main.py` | L55–56 | `traceback.print_exc()` / `print(f"CRITICAL ERROR...")` | `logger.critical(..., exc_info=True)` |

> **UPDATE (v2.0):** All unstructured `print()` and `traceback` calls have been replaced with the standardized `get_logger(__name__)` utility. This ensures 100% log aggregation compatibility with external sinks (File, Console, and future OTel exporters).

### 3.2 ~~Error Handling Anti-patterns (Rule 2.2)~~ ✅ ADDRESSED (v2.0)

| File | Lines | Issue | Fix |
|:---|:---|:---|:---|
| `graph.py` | L74, L85, L93 | Bare `except Exception` returns `None` — no logging, no context | Add `logger.warning(f"...: {e}")` inside each handler |
| `graph.py` | L117–122 | Double-nested bare `except` — impossible to debug | Flatten to single try/except with structured error message |
| `graph.py` | L339 | `except Exception: pass` — fails silently in guardrail extraction | Log warning: guardrail parsing failure should be visible |
| `endpoints.py` | L68–73 | Exception detail leaked to client in HTTP response body | Return generic message; log full error server-side only (Rule 6.6.4) |

> **UPDATE (v2.0):** Resolved all bare `except` blocks. Implemented context-aware error chaining using `raise ... from e` and standardized `CustomException(e, sys)` for deep traceback capture in the logging stack.

### 3.3 ~~Hardcoded Values & Magic Numbers (Rule 2.3)~~ ✅ ADDRESSED (v2.0)

| Location | Value | Recommended Source |
|:---|:---|:---|
| `endpoints.py:57–62` | Risk thresholds `0.3`, `0.7` | `params.yaml → risk_thresholds` |
| `data_transformation.py:89` | `target_col = "target"` | `schema.yaml → target_column` (already available via `ConfigurationManager`) |
| `model_trainer.py:41` | `target_col = "target"` | Same as above |
| `data_transformation.py:92–96` | `cols_to_drop` hardcoded list | `config.yaml → data_transformation.cols_to_drop` |
| `build_features.py:50` | `10.0` cap for insolvent entities | `params.yaml → feature_params.insolvent_cap` |
| `graph.py:328` | Mora threshold `0.20` | `params.yaml → risk_thresholds.mora_critical` |
| `graph.py:334` | Liquidity threshold `0.50` | `params.yaml → risk_thresholds.current_ratio_critical` |

> **UPDATE (v2.0):** Migrated all business logic thresholds and magic numbers to `params.yaml`. Data scientists can now tune risk appetites and feature engineering caps without modifying the Python source code.

### 3.4 ~~Data Loading Performance (Rule 1.3)~~ ✅ ADDRESSED (v2.0)

| File | Issue | Impact |
|:---|:---|:---|
| `lookup_tool.py:36` | Loads entire CSV on **every** tool call — no caching | Redundant I/O under concurrent agent requests |
| `ml_api_tool.py:42` | Same: full CSV load per prediction request | Memory pressure in multi-request scenarios |

> **UPDATE (v2.0):** Implemented `@functools.lru_cache(maxsize=1)` for I/O-heavy data loading helpers. Disk I/O is now minimized to a single read operation, significantly improving agent tool responsiveness.

### 3.5 ~~Stack Trace Leakage (Rule 6.6.4)~~ ✅ ADDRESSED (v2.0)

~~`endpoints.py:72` returns the raw exception string to the client:~~
```python
detail=f"Prediction failed: {str(e)}"
```

~~This exposes internal implementation details (file paths, model errors, library names). Per Rule 6.6.4, unhandled exceptions MUST return a generic `500` body; full details are logged server-side only.~~

> **UPDATE (v2.0):** Implemented a global exception handler in `main.py` and sanitized the `/predict` endpoint. Clients now receive a standard `500 Internal Server Error` message while engineers retain full visibility via high-fidelity server logs.

---

## 4. Open Gaps — Tier 2: Elite Maturity Enhancements 🟡

These gaps distinguish a "production-ready" system from an "industry-reference" architecture.

### 4.1 No OpenTelemetry Tracing (Rule 4.2) ⭐ HIGHEST PRIORITY

The system relies entirely on `print()` and `RotatingFileHandler` for observability. Per Rule 4.2, every production agentic system MUST implement structured, exportable tracing using OTel.

**What's missing:**
- No `src/utils/telemetry.py` bootstrap module (Rule 4.2.1)
- No root/child span hierarchy on agent invocations (Rule 4.2.2)
- No `gen_ai.*` semantic conventions on LLM/tool calls (Rule 4.2.3)
- No RED metrics instruments (`agent.request.count`, `agent.request.duration`, etc.) (Rule 4.2.4)
- No `FastAPIInstrumentor` registration in lifespan (Rule 6.3)

**Implementation Roadmap:**
1. Add OTel dependencies to `pyproject.toml`
2. Create `src/utils/telemetry.py` with `configure_tracer()`
3. Register `FastAPIInstrumentor` in `lifespan()`
4. Wrap `invoke_with_fallback()` with `tracer.start_as_current_span("llm_call")`
5. Wrap each tool function with child spans (`gen_ai.tool.name` attributes)
6. Add `suppress_otel_export` autouse fixture to `tests/conftest.py` (Rule 4.4)

### 4.2 Prompts in Python Module, Not External Files (Rule 1.5)

Prompts are centralized in `src/agents/prompts.py` (good), but Rule 1.5 mandates prompts be stored in **external files** within a dedicated directory structure for clean versioning.

**Current:**
```
src/agents/prompts.py  ← Python string constants
```

**Required (Rule 1.5):**
```
src/agents/prompts/
├── system_prompts/
│   ├── financial_analyst_v1.txt
│   ├── data_scientist_v1.txt
│   └── orchestrator_v1.txt
└── prompt_loader.py
```

**Impact:** Lower — functionally equivalent. But external files enable non-engineer stakeholders to review/edit prompts, and Git diffs on `.txt` files are cleaner than Python string diffs.

### 4.3 `ConfigBox` — Untyped Config Access (Rule 2.3)

`read_yaml()` returns `ConfigBox` (python-box), which provides attribute-style access but **zero type safety**. A typo like `config.modl_trainer` silently returns `None` / `Box()` instead of raising an error.

**Impact:** Undermines the typed entity layer. `ConfigurationManager` bridges the gap by constructing typed `@dataclass` entities, but the intermediate `ConfigBox` layer is an untyped hole.

**Recommended migration:**
```python
# Replace ConfigBox with Pydantic BaseModel for YAML parsing
class PipelineConfig(BaseModel):
    artifacts_root: str
    data_ingestion: DataIngestionYamlConfig
    data_validation: DataValidationYamlConfig
    # ...

config = PipelineConfig(**yaml.safe_load(f))
```

### 4.4 No API Versioning (Rule 6.3)

Endpoints are mounted at `/health` and `/predict` without a version prefix. Rule 6.3 mandates all endpoints under `/v1/`.

**Current:** `router = APIRouter()` → mounts at `/health`, `/predict`
**Required:** `router = APIRouter(prefix="/v1")` → mounts at `/v1/health`, `/v1/predict`

**Impact:** Trivial to implement, but signals production awareness and enables backward-compatible API evolution.

### 4.5 No Security Headers Middleware (Rule 6.6.4)

FastAPI responses do not include mandatory security headers:

| Header | Status |
|:---|:---|
| `X-Content-Type-Options: nosniff` | ❌ Missing |
| `X-Frame-Options: DENY` | ❌ Missing |
| `Strict-Transport-Security` | ❌ Missing |
| `Content-Security-Policy` | ❌ Missing |

**Action:** Add `SecurityHeadersMiddleware` to `main.py` as app-level middleware.

### 4.6 No Rate Limiting (Rule 6.6.4)

The `/predict` endpoint accepts unbounded requests. Per Rule 6.6.4, every public-facing endpoint MUST implement rate limiting via `slowapi`.

### 4.7 Coverage Threshold Below Standard (Rule 4.1.3)

Current CI gate: `--cov-fail-under=40`. Rule 4.1.3 mandates **≥65%** for early-phase projects and **≥85%** for production-grade pipelines.

**Action:** Progressively raise the threshold: 40% → 65% (next sprint) → 85% (production milestone).

### 4.8 No `Makefile` / Developer Orchestration (Rule 6.5)

No standardized entry point for common development commands. Rule 6.5 mandates a centralized launcher.

**Proposed `Makefile`:**
```makefile
.PHONY: lint test typecheck docker pipeline validate

lint:
	uv run ruff check . && uv run ruff format --check .

typecheck:
	uv run pyright src/

test:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing

docker:
	docker compose up --build

pipeline:
	uv run dvc repro

validate: lint typecheck test
```

### 4.9 No Pre-commit Hooks (Rule 6.2)

No `.pre-commit-config.yaml` exists. Pre-commit hooks prevent lint/type issues from reaching CI.

### 4.10 No Great Expectations (GX) Data Validation (Rule 2.11)

`DataValidation` component (`data_validation.py`) only checks column presence and dtype matching. Production-grade validation requires:
- Value range constraints (e.g., `revenue_growth ∈ [-1.0, 10.0]`)
- Null percentage thresholds per column
- Distribution drift detection (PSI — Rule 2.14.3)

**Action:** Augment with GX expectation suites stored as versioned artifacts alongside the DVC pipeline.

### 4.11 No LLM-as-a-Judge Evaluation (Rule 4.1.4)

No automated qualitative evaluation of agent-generated credit reports. Rule 4.1.4 mandates scoring on four axes:

| Dimension | Status |
|:---|:---|
| Relevance | ❌ Not evaluated |
| Faithfulness | ❌ Not evaluated |
| Tool Usage | ❌ Not evaluated |
| Business Value Alignment | ❌ Not evaluated |

**Action:** Create a golden dataset of 20+ (input, expected_output) pairs. Implement an eval harness using DeepEval or a custom LLM-as-a-Judge in `reports/docs/evaluations/`.

### 4.12 Docker Base Image Not Pinned by Digest (Rule 6.6.3)

```dockerfile
# Current (mutable tag):
FROM python:3.10-slim-bookworm AS runtime

# Required (immutable digest):
FROM python:3.10-slim-bookworm@sha256:abc123... AS runtime
```

### 4.13 No Vulnerability Scanning in CI (Rule 6.6.3)

No Docker Scout or Trivy step in `.github/workflows/ci.yml`. Rule 6.6.3 mandates vulnerability scanning as a blocking CI gate.

### 4.14 ~~`model_registration.py` Logger Inconsistency~~ ✅ ADDRESSED (v2.0)

~~Uses `from src.utils.common import logger` while all other modules use `get_logger(__name__)`. This breaks structured log filtering by module name.~~

> **UPDATE (v2.0):** Standardized logger initialization to use `get_logger(__name__)`. Module-name filtering now functions correctly across the entire codebase.

### 4.15 No `extra="forbid"` on API Schemas (Rule 6.3)

`PredictionInput` and `PredictionOutput` use `ConfigDict(populate_by_name=True)` but do not set `extra="forbid"`. This allows unknown fields to pass validation silently.

### 4.16 Health Endpoint Missing `model_version` (Rule 6.3)

`GET /health` returns `{"status": "ok", "service": "ACRAS-API"}` but does not include `model_version`, which Rule 6.3 mandates for deployment verification.

### 4.17 No Pytest Markers Registered (Rule 4.4)

`pyproject.toml` does not register custom markers (`unit`, `integration`, `eval`). Rule 4.4 mandates marker registration for targeted test execution.

### 4.18 GitHub Actions `uses:` Not Pinned to SHA (Rule 6.2)

CI workflow uses tag-based action references (`actions/checkout@v6`, `astral-sh/setup-uv@v7`). Rule 6.2 mandates pinning to full commit SHA to prevent supply chain attacks.

---

## 5. Prioritized Action Plan

### Phase 1: Foundation & Critical Resolution ✅ COMPLETE

- [x] **Gitignore & Environment Safety** (§6.6.1) — Added `.env.example`, gitignored `.env`, and documented key rotation guidance.
- [x] **Static Type Enforcement** (§2.3) — Integrated `pyright` in CI, added `[tool.pyright]` config, and `py.typed` marker.
- [x] **Core Test Coverage** (§4.1) — Added 5 missing component test modules and installed `pytest-cov` fail-fast gate.
- [x] **Dependency Integrity** (§6.6.3) — Added `pydantic-settings` to `pyproject.toml` and verified `uv.lock` consistency.
- [x] **Package Structure** (§2.10) — Propagated `__init__.py` files across all modules in `src/` and `tests/`.

### Phase 2: Sprint 1 — Operational Hardening 🔴 HIGH PRIORITY - COMPLETE ✅ 

- [x] **Structured Logging** (§4.2) — Replace all `print()` with `logger.*()` in `graph.py`, `endpoints.py`, and `main.py` for log aggregation compatibility.
- [x] **Defensive Error Handling** (§2.2) — Fix bare `except` blocks and implement `raise ... from e` to preserve trace context in `graph.py`.
- [x] **Security Boundary Hardening** (§6.6.4) — Implement generic 500 error responses and sanitize API details to prevent internal stack trace leakage.
- [x] **Parameter Extraction** (§2.3) — Move hardcoded risk thresholds (0.3, 0.7) and magic numbers to `params.yaml` via `ConfigurationManager`.
- [x] **Tool Performance Optimization** (§1.3) — Implement `@lru_cache` for data loading in `lookup_tool.py` and `ml_api_tool.py` to reduce I/O pressure.
- [x] **Logger Standardization** (§2.1) — Fix inconsistent logger import in `model_registration.py` to ensure correct module-name filtering.

### Phase 3: Sprint 2 — Elite Infrastructure 🟡 MEDIUM PRIORITY

- [ ] **OpenTelemetry Tracing** (§4.2) — Implement `src/utils/telemetry.py` and instrument FastAPI/LangGraph spans with `gen_ai.*` semantic conventions.
- [ ] **API Versioning** (§6.3) — Prefix all routes with `/v1/` and include `model_version` in the `/health` response.
- [ ] **Global Security Middleware** (§6.6.4) — Add `SecurityHeadersMiddleware` and rate limiting (`slowapi`) to the FastAPI application.
- [ ] **Strict Schema Validation** (§6.3) — Add `extra="forbid"` to all Pydantic models to prevent unknown payload fields.
- [ ] **Test Quality Gates** (§4.1.3) — Raise CI coverage threshold to 65% and register custom markers (`unit`, `integration`, `eval`) in `pyproject.toml`.
- [ ] **Unified Orchestration (Makefile)** (§6.5) — Create a root-level `Makefile` to consolidate `lint`, `test`, `typecheck`, and `pipeline` commands.

### Phase 4: Sprint 3 — Advanced Maturity & Portfolio Differentiation 🟢

- [ ] **Prompt Decoupling** (§1.5) — Migrate system prompts from Python modules to versioned `.txt` files in `src/agents/prompts/`.
- [ ] **Typed Configuration Migration** (§2.3) — Replace `ConfigBox` with Pydantic `BaseModel` for YAML parsing to ensure compile-time type safety.
- [ ] **Statistical Data Validation** (§2.11) — Integrate Great Expectations (GX) for distribution-based data contracts in the DVC pipeline.
- [ ] **LLM-as-a-Judge Evaluation** (§4.1.4) — Build an automated qualitative scoring harness for risk reports using DeepEval.
- [ ] **Supply Chain Hardening** (§6.6.3) — Pin Docker base images by digest and GitHub Actions by full commit SHA.
- [ ] **Automated Vulnerability Scanning** (§6.6.3) — Integrate Trivy or Docker Scout into the CI/CD pipeline as a blocking gate.

---

## 6. Summary Scorecard

**Overall: 8.4/10 → 8.9/10 (Operational Hardening Complete)**

---

## 6. Summary Scorecard

| Category | v1.1 | v2.0 | Key Evidence |
|:---|:---:|:---:|:---|
| **Architecture** | 9.5/10 | 9.5/10 | FTI pattern, Brain/Brawn separation |
| **Agentic Design** | 9/10 | 9/10 | 3-tier fallback, Strategy pattern factory |
| **Code Quality** | 7.5/10 | **9.5/10** | ✅ `print()` removed, magic numbers extracted |
| **Type Safety** | 9/10 | 9/10 | `pyright` CI gate, `py.typed`, typed entities |
| **Testing** | 8/10 | 8/10 | 17 test files, 3-tier CI |
| **CI/CD** | 8/10 | 8/10 | Parallel jobs, lint→test gating |
| **Security** | 7.5/10 | **8.5/10** | ✅ Stack trace leak fixed, generic 500s |
| **Observability** | 5/10 | **7.5/10** | ✅ Structured logging integrated everywhere |
| **Documentation** | 9.5/10 | 9.5/10 | Five Pillars taxonomy |
| **DevOps Maturity** | 8.5/10 | **9.0/10** | ✅ Performance optimizations (§3.4) |

**Overall: 8.4/10 → 8.9/10** — Sprint 1 (Operational Hardening) is complete. Code quality and security scores have seen significant improvements.

---

## 7. Rules Compliance Matrix

| Rule | Description | Status | Notes |
|:---|:---|:---:|:---|
| **1.2** | Brain vs. Brawn separation | ✅ | Agents reason; tools calculate |
| **1.3** | Tools as Microservices (Pydantic inputs) | ✅ | Tool performance optimized via caching |
| **1.4** | Structured Output Enforcement | ⚠️ | Guardrails exist but no JSON-mode output |
| **1.5** | No Naked Prompts (external files) | ⚠️ | Centralized in `.py`, not external `.txt` |
| **1.6** | State Persistence & HITL | ℹ️ | Not applicable for current scope |
| **1.7** | Prompt Engineering as First-Line Debug | ✅ | Prompt versioning supports iteration |
| **1.8** | Agent Patterns (Sequential/Strategy) | ✅ | Relay Team + Strategy factory |
| **2.2** | Defensive Error Handling | ✅ | Bare `except` blocks eliminated |
| **2.3** | Typed schemas everywhere | ⚠️ | Magic numbers moved to config |
| **2.14** | FTI Pipeline | ✅ | 7-stage DVC pipeline |
| **4.1** | Testing Pyramid | ✅ | Unit + Integration + API layers |
| **4.1.3** | Coverage ≥65% | ❌ | Currently 40% threshold |
| **4.1.4** | LLM-as-a-Judge Evals | ❌ | Not implemented |
| **4.2** | OpenTelemetry Tracing | ❌ | Not implemented |
| **4.4** | Test Infrastructure Hygiene | ⚠️ | No markers, no OTel suppression fixture |
| **5.1** | Five Pillars Documentation | ✅ | Full taxonomy |
| **6.1** | Docker Hardening | ⚠️ | Good structure; base not digest-pinned |
| **6.2** | CI Pipeline | ⚠️ | No vuln scan, no SHA pinning |
| **6.3** | FastAPI Standards | ⚠️ | No `/v1/` prefix, no `model_version` in health |
| **6.4** | Multi-Point Validation Gate | ❌ | No `validate_system` script |
| **6.5** | Standardized Orchestration (Makefile) | ❌ | No Makefile |
| **6.6.1** | Secret Management | ✅ | `.env.example`, keys gitignored |
| **6.6.3** | Supply Chain Integrity | ⚠️ | `uv.lock` committed; images not digest-pinned |
| **6.6.4** | API Boundary Hardening | ⚠️ | Generic 500s added; no rate limit yet |

**Legend:** ✅ Compliant | ⚠️ Partial | ❌ Missing | ℹ️ N/A
