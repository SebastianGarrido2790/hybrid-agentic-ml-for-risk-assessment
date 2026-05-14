# LLM-as-a-Judge Evaluation — Technical Implementation Workflow

**Project:** Hybrid Agentic ML for Risk Assessment (ACRAS)
**Document Type:** Workflow · The How
**Version:** 1.1
**Date:** 2026-05-13
**Status:** Production (Advanced Maturity — Sprint 3)

---

## 1. Purpose & Scope

This document is the **technical source of truth** for the LLM-as-a-Judge evaluation harness implemented in `src/evals/`. It covers every implementation decision at the code level: module responsibilities, data flow through Pydantic schemas, error handling contracts, test coverage strategy, and the step-by-step procedure for executing and extending the evaluation suite.

For the architectural overview and design rationale, see `reports/docs/architecture/llm_judge_architecture.md`.

---

## 2. File Inventory

| File | Module Type | Responsibility |
| :--- | :--- | :--- |
| `src/evals/__init__.py` | Package | Package declaration |
| `src/evals/schemas.py` | Data Layer | All Pydantic models for the eval pipeline |
| `src/evals/golden_dataset.json` | Data Layer | 20 curated golden (input, expected_output) pairs |
| `src/evals/judge_harness.py` | Orchestration | Pipeline coordinator: load → invoke → judge → gate → report |
| `src/agents/prompts/system_prompts/llm_judge_v1.txt` | Config | Versioned judge system prompt |
| `scripts/run_evals.py` | CLI Entry Point | Argument parsing, report persistence, MLflow logging |
| `tests/unit/test_eval_harness.py` | Test Layer | 22 deterministic unit tests (zero API cost) |
| `src/components/eval_dataset_validation.py` | Component | Standardized validation logic for golden dataset |
| `src/pipeline/stage_07_eval_dataset_validation.py` | Pipeline | DVC orchestration for the validation stage |
| `src/agents/monitoring.py` | Runtime | Real-time monitoring judge node implementation |

---

## 3. Schema Layer — `src/evals/schemas.py`

### 3.1 Design Principles

All schemas enforce `extra="forbid"`. This means any unexpected field from the LLM Judge response, a malformed JSON payload, or an incorrectly structured golden dataset entry will raise a `ValidationError` immediately — not silently ignored. This is the primary data quality gate in the eval pipeline.

### 3.2 `GoldenSample`

The input contract for every evaluation scenario. Validated at dataset load time via `load_golden_dataset()`.

```python
class GoldenSample(BaseModel):
    model_config = {"extra": "forbid"}

    sample_id: str                                           # "GD-001" format
    company_id: int                                          # val.csv ID
    scenario_description: str                                # Human-readable test intent
    input_query: str                                         # Verbatim query to ACRAS agent
    expected_keywords: list[str]                             # Min 3 keywords (min_length=3)
    expected_recommendation: Literal["APPROVE", "REJECT", "REVIEW"]
    expected_risk_tier: Literal["LOW", "MEDIUM", "HIGH"]
    ground_truth_ratios: dict[str, float]                    # For faithfulness context
```

**Key constraints:**
- `expected_recommendation` and `expected_risk_tier` are `Literal` types — Pydantic rejects any value not in the allowed set at dataset load time, not at runtime.
- `expected_keywords` has `min_length=3` to enforce that each scenario provides enough signal for the judge's relevance assessment.

### 3.3 `DimensionScore`

The atomic unit of the judge's evaluation. Each of the four axes produces one `DimensionScore`.

```python
class DimensionScore(BaseModel):
    model_config = {"extra": "forbid"}

    score: int = Field(..., ge=1, le=5)      # Rejects 0 or 6 at validation time
    justification: str                        # One-sentence rationale from the judge
    pass_threshold: int                       # Injected by harness if LLM omits it
```

The `ge=1, le=5` constraint on `score` means the `DimensionScore` schema is itself the guard against out-of-range judge outputs — no additional validation code is needed.

### 3.4 `JudgeVerdict`

The complete structured output from the LLM Judge for a single evaluation. It is the Pydantic model that enforces the JSON-only output contract.

```python
class JudgeVerdict(BaseModel):
    model_config = {"extra": "forbid"}

    relevance: DimensionScore        # Threshold ≥ 4
    faithfulness: DimensionScore     # Threshold ≥ 4
    tool_usage: DimensionScore       # Threshold ≥ 4
    business_value: DimensionScore   # Threshold ≥ 3
    overall_summary: str
```

### 3.5 `EvalResult` and `EvalSuiteReport`

`EvalResult` is the per-sample output container. It holds the agent's raw response text alongside the judge's verdict and the deterministic PASS/FAIL flag:

```python
class EvalResult(BaseModel):
    sample_id: str
    company_id: int
    agent_response: str
    judge_verdict: JudgeVerdict | None = None   # None only on error
    passed: bool = False
    eval_timestamp: datetime
    error: str | None = None                    # Populated only when agent or judge raises
```

`EvalSuiteReport` is the aggregated suite output that gets persisted to JSON and logged to MLflow:

```python
class EvalSuiteReport(BaseModel):
    suite_version: str                # From golden_dataset.json "version" field
    total_samples: int
    passed_samples: int
    failed_samples: int
    pass_rate: float                  # Constrained: ge=0.0, le=1.0
    mean_relevance: float
    mean_faithfulness: float
    mean_tool_usage: float
    mean_business_value: float
    results: list[EvalResult]
```

---

## 4. Harness Implementation — `src/evals/judge_harness.py`

### 4.1 Module Constants

```python
GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
DATASET_VERSION = "1.0.0"

_THRESHOLDS: dict[str, int] = {
    "relevance": 4,
    "faithfulness": 4,
    "tool_usage": 4,
    "business_value": 3,
}
```

The `_THRESHOLDS` dict is the **single source of truth** for pass/fail criteria. It is used in two places: `_parse_judge_response()` (to inject missing `pass_threshold` values) and `_check_thresholds()` (for the deterministic gate). Any future threshold change must be made here and here only.

### 4.2 `load_golden_dataset()`

```python
def load_golden_dataset(path: Path = GOLDEN_DATASET_PATH) -> list[GoldenSample]:
```

Reads and Pydantic-validates the entire golden dataset at call time. Raises `FileNotFoundError` if the JSON is missing and `ValidationError` if any sample fails schema validation. The failure is loud and immediate — a corrupt or malformed dataset cannot silently enter the pipeline.

### 4.3 `_invoke_acras_agent()`

```python
def _invoke_acras_agent(sample: GoldenSample) -> str:
```

Invokes the full ACRAS LangGraph relay (`src/agents/graph.py`) end-to-end for a single sample. The graph import is deferred to call time (inside the function body) to avoid circular imports at module load. The function:

1. Constructs `state_input` with `HumanMessage(sample.input_query)` and `company_id`.
2. Calls `app.invoke(state_input)`. The `# type: ignore[arg-type]` annotation at this call site whitelists a known pyright/LangGraph TypedDict compatibility issue at the dynamic import boundary.
3. Extracts the last message from `result["messages"]` as the credit report text.
4. Raises `RuntimeError` if the agent returns no messages.

**Error containment:** Any exception from this function is caught in `evaluate_sample()` and recorded as `EvalResult(passed=False, error="Agent error: ...")`. The suite continues to the next sample.

### 4.4 `_build_judge_user_prompt()`

```python
def _build_judge_user_prompt(sample: GoldenSample, agent_response: str) -> str:
```

Constructs the structured user-turn message for the judge. It injects three information blocks:

1. **Evaluation Context:** The scenario description and the original user query, so the judge understands what a correct response should address.
2. **Ground Truth:** The expected recommendation, expected risk tier, expected keywords, and ground truth financial ratios — giving the judge the reference data needed for faithfulness and relevance scoring.
3. **Agent Response:** The full credit report text to be evaluated.

The prompt ends with a hard instruction: *"Return ONLY the JSON object — no markdown fences, no prose outside the JSON."* The markdown fence stripping in `_parse_judge_response()` handles cases where the model ignores this instruction.

### 4.5 `_parse_judge_response()`

```python
def _parse_judge_response(raw: str) -> JudgeVerdict:
```

The JSON parsing and validation gate. Implemented in three steps:

**Step 1 — Markdown fence stripping:**
```python
cleaned = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE).strip()
cleaned = cleaned.rstrip("`").strip()
```
This regex matches both ` ```json ` and ` ``` ` opening fences and the trailing ` ``` `. The double strip removes residual whitespace. This handles the most common model non-compliance pattern without relaxing the JSON schema contract.

**Step 2 — JSON parsing:**
```python
data = json.loads(cleaned)
```
On `JSONDecodeError`, raises a `ValueError` with the first 500 characters of the raw response for debugging. The error propagates up to `evaluate_sample()` which catches it and records it as a judge error.

**Step 3 — Threshold injection:**
```python
for dim, threshold in _THRESHOLDS.items():
    if dim in data and "pass_threshold" not in data[dim]:
        data[dim]["pass_threshold"] = threshold
```
If the judge LLM omits `pass_threshold` from any dimension (which it may, since it is an internal harness field, not a field the judge would naturally include), the harness injects the canonical value from `_THRESHOLDS`. This prevents `ValidationError` on a structurally valid but incomplete response, while maintaining the correctness of all threshold comparisons.

**Step 4 — Pydantic validation:**
```python
return JudgeVerdict(**data)
```
Any unexpected field, wrong type, or out-of-range score raises `ValidationError` here. The error propagates as a judge error in `evaluate_sample()`.

### 4.6 `_invoke_judge()`

```python
def _invoke_judge(sample: GoldenSample, agent_response: str) -> JudgeVerdict:
```

Instantiates a **tool-free** Gemini Flash instance via `get_llm(provider="gemini")`. No tools are bound — the judge must reason from context only, preventing any side-effects. The judge receives:

- `SystemMessage(system_prompt)` — loaded from `llm_judge_v1.txt` via `get_prompt()`.
- `HumanMessage(user_message)` — constructed by `_build_judge_user_prompt()`.

Gemini's list-format content normalization is applied before passing to `_parse_judge_response()`, matching the same normalization used in `invoke_with_fallback()` in `graph.py`.

### 4.7 `_check_thresholds()` — The Deterministic Gate

```python
def _check_thresholds(verdict: JudgeVerdict) -> bool:
```

This function is the **Brawn** of the evaluation pipeline. It applies four integer comparisons and logs each result:

```python
dimensions: dict[str, DimensionScore] = {
    "relevance": verdict.relevance,
    "faithfulness": verdict.faithfulness,
    "tool_usage": verdict.tool_usage,
    "business_value": verdict.business_value,
}
all_passed = True
for dim_name, dim_score in dimensions.items():
    passed = dim_score.score >= dim_score.pass_threshold
    ...
    if not passed:
        all_passed = False
return all_passed
```

Critical properties:
- **No LLM involved.** The PASS/FAIL decision is 100% deterministic.
- **All-or-nothing.** A score of 4/4 on relevance, faithfulness, and tool usage, but 2/3 on business value → `False`. One missed threshold fails the sample.
- **Log-visible.** Each dimension's result is logged at `INFO` level with the score, threshold, and justification — enabling immediate diagnosis without opening the JSON report.

### 4.8 `evaluate_sample()`

```python
def evaluate_sample(sample: GoldenSample, dry_run: bool = False) -> EvalResult:
```

The per-sample coordinator. In `dry_run=False` mode:

1. Calls `_invoke_acras_agent(sample)` — catches any exception, returns a failed `EvalResult` with `error="Agent error: ..."`.
2. Calls `_invoke_judge(sample, agent_response)` — catches any exception, returns a failed `EvalResult` with `error="Judge error: ..."`.
3. Calls `_check_thresholds(verdict)` to set `passed`.
4. Returns a complete `EvalResult`.

In `dry_run=True` mode, steps 1 and 2 are skipped entirely. A synthetic `JudgeVerdict` with all dimensions at their minimum passing thresholds is returned immediately. The `patch` assertions in `test_evaluate_sample_dry_run_no_api_calls` verify that no LLM functions are called in this mode.

### 4.9 `run_eval_suite()`

```python
def run_eval_suite(
    samples: list[GoldenSample] | None = None,
    dry_run: bool = False,
) -> EvalSuiteReport:
```

Iterates over all samples, collects `EvalResult` objects, and aggregates them. Mean score computation:

```python
def _mean(attr: str) -> float:
    if not scored:
        return 0.0
    return sum(getattr(r.judge_verdict, attr).score for r in scored) / len(scored)
```

Only samples with a non-`None` `judge_verdict` are included in the mean score computation, ensuring that samples that errored (e.g., agent unavailable) do not skew the aggregate metrics toward zero.

---

## 5. Judge System Prompt — `llm_judge_v1.txt`

The judge prompt follows the structured sectioning standard. It defines:

1. **Role:** Impartial Credit Risk Report Evaluator.
2. **Evaluation Axes:** Four axes with precise per-score descriptions (1–5 Likert scale definitions for each axis).
3. **Output Contract:** JSON-only. The required schema is specified directly in the prompt with placeholder types, mirroring the `JudgeVerdict` Pydantic model.

**Excerpt — Faithfulness Axis Definition:**
```text
### 2. Faithfulness (Threshold: 4/5)
Are all quantitative claims grounded in the retrieved financial data? No hallucinated metrics.
- 5: Every number cited is verifiably from the input context; no hallucinations.
- 4: All key numbers correct; trivial formatting differences only.
- 3: Minor factual errors or one unverified claim.
- 2: Multiple hallucinated values or contradicts retrieved data.
- 1: Fabricated data; cannot be trusted.
```

**Prompt Upgrade Procedure:** Create `llm_judge_v2.txt` with the revised criteria. Update the `get_prompt("system_prompts", "llm_judge_v1.txt")` call in `_invoke_judge()` to `"llm_judge_v2.txt"`. Re-run the full suite. Log the eval delta to MLflow. Commit both files.

---

## 6. CLI Runner — `scripts/run_evals.py`

### 6.1 Argument Reference

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--dry-run` | `False` | Skip all LLM calls; return synthetic passing results |
| `--sample-ids GD-001 GD-005` | All 20 | Evaluate only the specified sample IDs |
| `--output-dir PATH` | `reports/docs/evaluations/` | Directory for the JSON report |
| `--log-mlflow` | `False` | Log aggregate metrics to MLflow |

### 6.2 Exit Codes

| Code | Meaning |
| :---: | :--- |
| `0` | All evaluated samples passed all dimension thresholds |
| `1` | One or more samples failed; check the JSON report for details |

The exit code `1` is designed to be caught by CI pipelines as a build failure. Any eval regression — a prompt change that degrades faithfulness, a model update that affects tool usage — surfaces immediately as a failed CI check.

### 6.3 Output Report Format

Each run persists a timestamped report at `reports/docs/evaluations/eval_report_<YYYYMMDD_HHMMSS>.json`. The structure maps directly to `EvalSuiteReport.model_dump()`:

```json
{
  "suite_version": "1.0.0",
  "run_timestamp": "2026-05-13T04:00:00.000000",
  "total_samples": 20,
  "passed_samples": 20,
  "failed_samples": 0,
  "pass_rate": 1.0,
  "mean_relevance": 4.6,
  "mean_faithfulness": 4.8,
  "mean_tool_usage": 4.5,
  "mean_business_value": 4.2,
  "results": [
    {
      "sample_id": "GD-001",
      "company_id": 1,
      "agent_response": "# Executive Credit Risk Assessment\n...",
      "judge_verdict": {
        "relevance": { "score": 5, "justification": "...", "pass_threshold": 4 },
        "faithfulness": { "score": 5, "justification": "...", "pass_threshold": 4 },
        "tool_usage": { "score": 4, "justification": "...", "pass_threshold": 4 },
        "business_value": { "score": 4, "justification": "...", "pass_threshold": 3 },
        "overall_summary": "..."
      },
      "passed": true,
      "eval_timestamp": "2026-05-13T04:00:32.123456",
      "error": null
    },
    ...
  ]
}
```

---

## 7. Test Coverage — `tests/unit/test_eval_harness.py`

### 7.1 Test Strategy

All 22 tests are purely deterministic — zero LLM API calls. The `dry_run=True` flag and `unittest.mock.patch` are used to isolate each component under test.

### 7.2 Test Inventory

| Test Function | Category | What It Verifies |
| :--- | :--- | :--- |
| `test_golden_dataset_file_exists` | Dataset | Physical file existence at expected path |
| `test_load_golden_dataset_returns_20_samples` | Dataset | Exactly 20 samples loaded and validated |
| `test_golden_dataset_all_sample_ids_unique` | Dataset | No duplicate `sample_id` values |
| `test_golden_dataset_covers_all_risk_tiers` | Dataset | LOW, MEDIUM, HIGH all represented |
| `test_golden_dataset_covers_all_recommendations` | Dataset | APPROVE, REJECT, REVIEW all represented |
| `test_golden_sample_schema_rejects_invalid_recommendation` | Schema | Literal type enforcement on `expected_recommendation` |
| `test_check_thresholds_all_pass` | Gate | Returns `True` when all four dimensions ≥ threshold |
| `test_check_thresholds_fails_on_low_relevance` | Gate | Returns `False` when relevance = 2 (below 4) |
| `test_check_thresholds_business_value_threshold_is_3` | Gate | Score of 3/3 on business value returns `True` |
| `test_check_thresholds_fails_on_low_business_value` | Gate | Score of 2/3 on business value returns `False` |
| `test_parse_judge_response_valid_json` | Parser | Valid JSON produces a correctly typed `JudgeVerdict` |
| `test_parse_judge_response_strips_markdown_fences` | Parser | ` ```json ... ``` ` fences are stripped before parsing |
| `test_parse_judge_response_raises_on_invalid_json` | Parser | Non-JSON input raises `ValueError` with `"not valid JSON"` |
| `test_parse_judge_response_injects_pass_threshold` | Parser | Missing `pass_threshold` fields are injected from `_THRESHOLDS` |
| `test_evaluate_sample_dry_run_passes` | E2E | Dry-run returns `passed=True` `EvalResult` with no error |
| `test_evaluate_sample_dry_run_no_api_calls` | E2E | `_invoke_acras_agent` and `_invoke_judge` are not called in dry-run |
| `test_run_eval_suite_dry_run_returns_report` | E2E | Full 20-sample dry-run returns `EvalSuiteReport` with 100% pass rate |
| `test_run_eval_suite_dry_run_subset` | E2E | 3-sample subset runs correctly with 100% pass rate |
| `test_evaluate_sample_handles_agent_error` | Error | Agent `RuntimeError` → `EvalResult(passed=False, error="Agent error:...")` |
| `test_evaluate_sample_handles_judge_error` | Error | Judge `RuntimeError` → `EvalResult(passed=False, error="Judge error:...")` |
| `test_dimension_score_rejects_out_of_range` | Schema | Scores of 0 or 6 raise `ValidationError` |
| `test_eval_suite_report_pass_rate_computed_correctly` | Schema | `pass_rate > 1.0` raises `ValidationError` |

### 7.3 Running Tests

```bash
# Run only eval harness tests (fast, zero API cost):
uv run pytest tests/unit/test_eval_harness.py -v -m unit

# Run full test suite (includes eval harness, 100 tests):
uv run pytest tests/ --cov=src --cov-fail-under=65

# Run full LLM-as-a-Judge eval suite (requires API keys, ~20 min):
make evals

# Validate pipeline wiring without API calls:
make evals-dry-run
```

---

## 8. Extending the Evaluation Layer

### 8.1 Adding New Golden Samples

1. Open `src/evals/golden_dataset.json`.
2. Add a new entry to the `"samples"` array following the `GoldenSample` schema.
3. Assign a unique `sample_id` (e.g., `"GD-021"`).
4. Verify the `company_id` exists in `artifacts/data_ingestion/val.csv`.
5. Run `make evals-dry-run` to confirm the new entry passes schema validation.
6. Commit the updated JSON file. DVC-track it if the dataset is tracked as a DVC artifact.

### 8.2 Upgrading the Judge Prompt

1. Create `src/agents/prompts/system_prompts/llm_judge_v2.txt` with the revised criteria.
2. Update the `get_prompt()` call in `_invoke_judge()`:
   ```python
   system_prompt = get_prompt("system_prompts", "llm_judge_v2.txt")
   ```
3. Run `make evals` (full suite) against the baseline and record the before/after metrics in MLflow.
4. Commit both the new prompt file and the harness change in the same commit.

### 8.3 Changing Pass Thresholds

Edit `_THRESHOLDS` in `judge_harness.py`. The change propagates to both the `pass_threshold` injection in `_parse_judge_response()` and the `_check_thresholds()` gate automatically. Update the judge system prompt (`llm_judge_v1.txt` header) to keep the documentation in sync.

### 8.4 Adding a New Evaluation Dimension

1. Add the new dimension field to `JudgeVerdict` in `schemas.py`.
2. Add the new dimension's threshold to `_THRESHOLDS`.
3. Add a scoring rubric for the new dimension to the judge system prompt.
4. Add a corresponding `_check_thresholds()` comparison (it iterates `dimensions` dict dynamically — add the new key there).
5. Add `test_check_thresholds_*` tests for the new dimension.
6. Update `EvalSuiteReport` to include a `mean_<dimension>` field and aggregation in `run_eval_suite()`.

---

## 9. Makefile Targets Reference

```makefile
evals-dry-run:
    uv run python scripts/run_evals.py --dry-run

evals:
    uv run python scripts/run_evals.py
```

| Target | Use When |
| :--- | :--- |
| `make evals-dry-run` | Always — before running the live suite, to confirm pipeline wiring |
| `make evals` | Pre-deployment — full qualitative gate against all 20 golden scenarios |
| `make evals --sample-ids GD-001 GD-005` | Spot-checking after a targeted prompt or tool change |

---

## 10. Dataset Integrity Validation (Stage 07)

Before any qualitative evaluation (batch or live), the ground truth integrity must be verified. This is handled by Stage 07 of the DVC pipeline.

### 10.1 Configuration — `src/entity/config_entity.py`
The validation stage uses `EvalDatasetConfig` (immutable dataclass) for internal access and `EvalDatasetYamlConfig` (Pydantic BaseModel) for YAML boundary validation.

### 10.2 Component Logic — `src/components/eval_dataset_validation.py`
The `EvalDatasetValidation` component:
1. Loads the `golden_dataset.json` via the harness.
2. Checks that the file is not empty and contains the required keys.
3. Touches a `status.txt` artifact upon success to signal completion to DVC.

### 10.3 Execution
```bash
uv run dvc repro eval_dataset_validation
```

## 11. Live Monitoring Integration

The LLM-as-a-Judge system is extended into the runtime environment via the **"Monitor-as-a-Node"** pattern.

### 11.1 Orchestration — `monitor_node`
In `src/agents/graph.py`, the `monitor_node` is added as a terminal step:
```python
workflow.add_node("monitor_node", monitor_node)
workflow.add_edge("orchestrator_node", "monitor_node")
workflow.add_edge("monitor_node", END)
```

### 11.2 Operation
1. The node extracts the CRO's final report.
2. It invokes `_invoke_judge()` from the harness.
3. It logs dimensions to the `acras_live_monitoring` experiment in MLflow.
4. It suppresses failures to ensure the user receives the report even if the monitoring judge fails.

---

## 12. Related Documents

| Document | Location | Relationship |
| :--- | :--- | :--- |
| LLM-as-a-Judge Architecture | `reports/docs/architecture/llm_judge_architecture.md` | Design rationale and component overview |
| Agentic Reasoning Engine Architecture | `reports/docs/architecture/agentic_reasoning_engine.md` | The ACRAS agent (system under test) |
| Codebase Review v2.0 | `reports/docs/evaluations/codebase_review_v2.0.md` | Gap 4.11 resolution; maturity score update |
| CI Pipeline Workflow | `reports/docs/workflows/ci_pipeline_report.md` | How to integrate `make evals` as a CI gate |
| Stage 07 Validation Report | `reports/docs/workflows/stage_07_eval_dataset_report.md` | Ground truth integrity validation details |
