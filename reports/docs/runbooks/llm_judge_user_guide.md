## LLM-as-a-Judge Evaluation User Guide

To use the **LLM-as-a-Judge Evaluation** harness, follow this quick-start guide. The system is designed to provide both zero-cost wiring validation and full qualitative scoring.

### 1. Prerequisites
Ensure your environment is configured with the necessary API keys and dependencies:
*   **API Key**: `GOOGLE_API_KEY` must be set in your `.env` or shell environment (required for the `make evals` target).
*   **Dependencies**: Run `make install` or `uv sync` to ensure Pydantic v2 and Gemini-related packages are installed.

### 2. Validate Wiring (Zero Cost)
Before running a live evaluation, always run a **dry-run**. This validates the golden dataset loading, Pydantic schema integrity, and the deterministic threshold logic without making any LLM calls.
```bash
# Option A: Using Make
make evals-dry-run

# Option B: Manual (Windows/PowerShell)
uv run python scripts/run_evals.py --dry-run
```
*   **Result**: Returns a 100% pass rate using synthetic data.
*   **Use Case**: CI/CD pipelines and local environment checks.

### 3. Run Full Qualitative Suite
To evaluate the agent against the 20-sample golden dataset using the LLM Judge:
```bash
# Option A: Using Make
make evals

# Option B: Manual (Windows/PowerShell)
$env:SKIP_LIVE_MONITORING=1; $env:PYTHONIOENCODING="utf-8"; uv run python scripts/run_evals.py --log-mlflow
```
*   **Execution Time**: ~15–20 minutes (orchestrates 20 full agent runs + 20 judge calls).
*   **Gate**: Returns **Exit Code 0** if all samples pass the four axis thresholds, or **Exit Code 1** if any sample fails.

### 4. Selective Spot-Checking
If you have modified a specific part of the agent (e.g., the Financial Analyst prompt) and only want to test relevant scenarios:
```bash
uv run python scripts/run_evals.py --sample-ids GD-001 GD-005 --log-mlflow
```
*   The `--sample-ids` flag filters the suite to specific IDs from `golden_dataset.json`.
*   The `--log-mlflow` flag ensures the results are tracked in your active MLflow experiment.

### 5. Analyzing Results
After a run, you can find the detailed results in two locations:

1.  **JSON Report**: Located in `artifacts/eval_dataset/eval_report_<timestamp>.json`. This contains the raw agent response, the judge's justification for every score, and the pass/fail status per sample.
2.  **MLflow**: Navigate to the `llm_judge_eval` experiment. You will see metrics for:
    *   `eval/pass_rate`
    *   `eval/mean_relevance`
    *   `eval/mean_faithfulness`
    *   `eval/mean_tool_usage`
    *   `eval/mean_business_value`

### 6. Extending the Dataset
To add a new test case, append a new entry to `src/evals/golden_dataset.json`. Use `make evals-dry-run` to confirm your new entry matches the `GoldenSample` Pydantic schema.

> [!TIP]
> For a deep dive into the scoring rubrics (1–5 Likert scales) or to upgrade the judge's instructions, refer to the **Technical Implementation Workflow** at `reports/docs/workflows/llm_judge_workflow.md`.