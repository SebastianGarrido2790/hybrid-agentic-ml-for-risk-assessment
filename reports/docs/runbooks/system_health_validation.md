# Workflow: System Health & Production Readiness Validation

**Document ID:** WF-09
**Type:** Technical Workflow
**Version:** 1.0
**Status:** Active

---

## 1. Overview

This workflow defines the mandatory **Multi-Point Validation** process that must be executed after any architectural shift, code modification, or dependency update in ACRAS. Following these steps ensures that the "Brain" (Agents) and "Hands" (Tools/Pipelines) remain in perfect synchronization and meet the project's production-grade quality gates.

---

## 2. The 5 Pillars of Validation

### Phase 1: Static Code Quality (The Gatekeeper)
Ensures the codebase adheres to strict typing and formatting standards before execution.

| Check | Command | Success Criteria |
| :--- | :--- | :--- |
| **Type Safety** | `uv run pyright src/` | `0 errors, 0 warnings` (Standard Mode) |
| **Linting** | `uv run ruff check .` | `All checks passed!` |
| **Formatting** | `uv run ruff format --check .` | `n files already formatted` |

### Phase 2: Functional Logic & Coverage (The Brawn)
Validates that deterministic tools and ML components perform correctly and meet coverage requirements.

| Check | Command | Success Criteria |
| :--- | :--- | :--- |
| **Unit Tests** | `uv run pytest tests/unit/ -v` | All 22+ tests `PASSED` |
| **Coverage Gate** | `uv run pytest --cov=src --cov-fail-under=40` | Total coverage ≥ 40% (Incremental) |

### Phase 3: Pipeline Synchronization (The Lineage)
Verifies that the DVC data/model management layer is in sync with the source code.

| Check | Command | Success Criteria |
| :--- | :--- | :--- |
| **DVC Status** | `uv run dvc status` | `Data and pipelines are up to date` |
| **Reproduction** | `uv run dvc repro` | Stages complete with no logic errors |

### Phase 4: API Service & Runtime (The Edge)
Confirms that the containerized (or local) prediction service is responsive and healthy.

| Check | Command | Success Criteria |
| :--- | :--- | :--- |
| **Liveness** | `curl -s http://localhost:8000/health` | `{"status":"ok", "service":"ACRAS-API"}` |
| **Integration** | `uv run pytest tests/integration/` | Cross-stage handoffs successful |

### Phase 5: Agentic Reliability (The Brain)
Ensures the LangGraph engine handles external provider failures gracefully.

| Check | Observation Method | Expected Behavior |
| :--- | :--- | :--- |
| **Fallback Logic** | Inspect logs/terminal during agent execution | `🤖 Agent -> Calling 1st Fallback...` message on provider failure |
| **Cost Awareness** | Monitor terminal for `402 Client Error` | System continues without halting via LLM cascading |

---

## 3. Post-Validation Checklist

- [ ] All 22 unit tests passed.
- [ ] Pyright reported 0 errors.
- [ ] DVC lockfile is synchronized with `src/`.
- [ ] API is returning `200 OK` responses.
- [ ] Documentation (`reports/docs/`) has been updated to reflect changes.

---

## 4. Automated Execution Script

For rapid validation, run the provided batch script:

```bash
.\validate_system.bat
```

Alternatively, run the following manually:

```bash
uv sync --extra dev && \
uv run pyright src/ && \
uv run ruff check . && \
uv run pytest tests/unit/ -v --cov=src --cov-fail-under=40 && \
uv run dvc status
```
