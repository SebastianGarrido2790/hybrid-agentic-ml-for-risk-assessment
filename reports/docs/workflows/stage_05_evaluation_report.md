# Stage 05: Model Evaluation Architecture Report

## Purpose
The **Model Evaluation Stage** is the final quality gate of the ACRAS training pipeline. It rigorously assesses the performance of the trained model using unseen data (`test.csv`) and generates both quantitative metrics and visual diagnostics to ensure the model's readiness for production.

## Workflow Logic
The evaluation stage integrates standard scikit-learn metrics with advanced MLflow tracking and automated visualization.

```mermaid
graph TD
    A[Test Dataset] --> B(Model Evaluation Component)
    M[acras_rf_model.joblib] --> B
    P[Hyperparameters] --> B
    B --> C[Metric Calculation]
    B --> D[ROC-AUC Visualization]
    C --> E[metrics.json]
    D --> F[roc_auc_curve.png]
    E --> G[MLflow Tracking]
    F --> G
```

## Evaluation Strategy

### 1. Performance Metrics
We calculate a comprehensive suite of metrics to evaluate the classifier from multiple perspectives:
*   **Accuracy**: Overall proportion of correct predictions.
*   **Precision**: Ability to avoid flagging low-risk companies as high-risk.
*   **Recall**: Ability to capture as many high-risk companies as possible (Critical for Risk).
*   **F1 Score**: Harmonic mean of Precision and Recall.
*   **ROC-AUC**: Measures the model's ability to distinguish between classes regardless of the probability threshold.

### 2. Visualization (ROC Curve)
The stage automatically generates a **Receiver Operating Characteristic (ROC)** curve.
*   **Local Artifact**: Saved as `artifacts/model_evaluation/roc_auc_curve.png`.
*   **Insight**: Helps the "Brain" (Agent) understand the trade-off between True Positive Rate and False Positive Rate.
*   **Robustness**: The plotting logic includes a fallback for imbalanced test sets (e.g., if only one class is present) to prevent pipeline failures.

### 3. MLflow Integration
Every evaluation run is logged as a unique experiment in MLflow for deep observability:
*   **Experiment**: `ACRAS_Risk_Assessment`
*   **Run Name**: Timestamped for traceability (e.g., `RF_Eval_2026_02_12_16_19`).
*   **Artifacts**: The model is logged under a descriptive name (`acras_risk_model`) and the ROC plot is attached to the run.

## Generated Artifacts
Location: `artifacts/model_evaluation/`
*   **`metrics.json`**: Machine-readable evaluation scores (used by DVC).
*   **`roc_auc_curve.png`**: Visual diagnostics of classifier performance.

## Operational Hardening (v2.0)
The evaluation stage now integrates with the global observability framework:

### 1. Structured Metric Logging
*   **Console & File Feed**: While metrics are saved to `metrics.json`, the evaluator now logs individual scores (Accuracy, Precision, Recall, ROC-AUC) at the `INFO` level using `get_logger(__name__)`.
*   **Traceability**: This allows for quick verification of model quality directly from the log stream without needing to open JSON artifacts.

### 2. Defensive Plotting
*   **Error Handling**: The plotting logic for ROC-AUC is now wrapped in `CustomException` handlers, ensuring that visual failures (e.g., display errors or headless environment issues) are caught and logged with full context rather than silently failing the pipeline.

## Why this is "Robust MLOps"
1.  **Robust Tracking**: Defaults to the local MLflow server with a SQLite backend for deep experiment history.
2.  **DVC Metrics**: Registering `metrics.json` allows for CLI-based performance comparisons (`dvc metrics diff`).
3.  **Automated Diagnostics**: Visual evidence of model quality is generated automatically, eliminating manual evaluation steps.
4.  **Operational Visibility**: High-level metrics are now part of the structured log stream, providing real-time quality feedback during pipeline execution.
