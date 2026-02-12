# MLflow workflow: Experiment Tracking & Model Management

The Agentic Credit Risk Assessment System (ACRAS) uses **MLflow** as its centralized "Experimentation Brain." This ensures that every model iteration, parameter tweak, and performance metric is recorded, versioned, and searchable.

## Why MLflow?
In an Agentic MLOps environment, the LLM ("The Brain") needs to inspect model performance history to make informed decisions. MLflow provides the API interface for both human engineers and AI agents to:
*   **Compare Experiments**: Instantly see which hyperparameters yielded the best recall.
*   **Trace Artifacts**: Link specific model weights to their evaluation plots.
*   **Register Models**: Promote successful candidates to a centralized "Model Registry."

## Architecture & Configuration

### 1. Centralized Resolution
We use a custom utility `get_mlflow_uri` (in `src/utils/mlflow_config.py`) to resolve the tracking server address. This utility follows a strict priority:
1.  **Environment Variable** (`MLFLOW_TRACKING_URI`).
2.  **Environment Defaults** (Production vs. Staging vs. Local).
3.  **YAML Configuration** (`config/params.yaml`).
4.  **Local Fallback** (`file:./mlruns`).

### 2. Experiment Structure
*   **Experiment Name**: `ACRAS_Risk_Assessment`
*   **Run Naming**: `RF_Eval_YYYY_MM_DD_HH_MM`
*   **Model Name**: `acras_risk_model`
*   **Registry Name**: `ACRAS_RandomForest_v1`

## Tracking Workflow

### Execution Flow
1.  The `ModelEvaluation` component calculates metrics.
2.  The system calls `get_mlflow_uri()` to find the active server.
3.  A new run is started under the `ACRAS_Risk_Assessment` experiment.
4.  **Parameters**: Logs `n_estimators`, `min_samples_leaf`, etc.
5.  **Metrics**: Logs `accuracy`, `precision`, `recall`, `f1_score`, and `roc_auc`.
6.  **Artifacts**:
    *   Saves the `roc_auc_curve.png` plot.
    *   Logs the trained model object using `mlflow.sklearn.log_model`.

### Observability
The system generates a direct link to the experiment run in the logs:
`[INFO] MLflow Run URL: http://127.0.0.1:5000/#/experiments/...`

## Environment Isolation
ACRAS is designed to run in multiple environments without code changes:
*   **Local**: Tracks to a local `./mlruns` directory or a local server.
*   **Staging/CI**: Tracks to a shared internal MLflow instance.
*   **Production**: Tracks to a secured remote server (e.g., DagsHub or Managed MLflow) via environment secrets.

## Best Practices Implemented
*   **Fault Tolerance**: The pipeline is "MLflow-Resilient." If the server is down, the component logs a warning but allows the local pipeline (DVC) to finish successfully.
*   **Strict Registry**: We use a naming convention for registered models that distinguishes between different architectures (e.g., `RandomForest_v1` vs `XGBoost_v1`).
*   **Decoupled Logic**: Tracking logic is separated from business logic, ensuring the `ModelEvaluation` component remains testable.
