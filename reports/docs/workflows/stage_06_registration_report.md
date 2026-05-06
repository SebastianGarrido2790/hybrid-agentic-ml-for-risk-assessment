# Stage 06: Model Registration Architecture Report

## Purpose
The **Model Registration Stage** acts as the final decision-maker in the ACRAS training pipeline. Its primary objective is to transition a high-performing model from a local artifact state into a centralized, versioned **Model Registry**. This ensures that only models meeting predefined performance thresholds are made available for downstream deployment services.

## Workflow Logic
This stage evaluates the model's metrics against a "quality gate" before interacting with the MLflow Model Registry.

```mermaid
graph TD
    subgraph "1. Configuration & Input"
        CONF[config.yaml] --> CM[ConfigurationManager]
        PAR[params.yaml] --> CM
        MET[metrics.json] --> NRC[ModelRegistrationComponent]
        MOD[acras_rf_model.joblib] --> NRC
        CM --> NRC
    end

    subgraph "2. Logic & Validation"
        NRC --> VAL{Metric Validation}
        VAL -- "ROC-AUC < Threshold" --> FAIL[Log Warning & Exit]
        VAL -- "ROC-AUC >= Threshold" --> CONN{MLflow Connection check}
    end

    subgraph "3. MLflow Action"
        CONN -- "Server Down" --> FALLBACK[Local Log & Gracious Fallback]
        CONN -- "Server Up" --> RUN[Start MLflow Run: 'Model_Registration_Stage']
        RUN --> LOG_M[Log Metrics to MLflow]
        LOG_M --> LOG_MOD[Log Model & Register]
    end

    subgraph "4. Output"
        LOG_MOD --> REG[Centralized Model Registry]
        REG --> VER[New Version Created: vN]
    end
```

## Implementation Details

### 1. The Quality Gate (Thresholding)
To prevent suboptimal models from reaching the registry, the component implements a hard threshold:
*   **Metric**: ROC-AUC
*   **Threshold**: `0.60` as global configuration (can be changed in `config/params.yaml`).
*   **Behavior**: If the model's ROC-AUC is below this value, the registration process is aborted with a warning. This ensures the integrity of the "Staging" and "Production" model pools.

### 2. MLflow Registry Integration
The component utilizes the `mlflow.sklearn.log_model` function with the `registered_model_name` parameter. This atomic operation:
1.  Uploads the model artifact (`.joblib`) to the MLflow tracking server.
2.  Creates a new version under the registered model name.
3.  Logs the final evaluation metrics directly to the registration run for traceability.

### 3. Fault-Tolerant Connection
In alignment with the "ACRAS" standards, the component includes a fallback mechanism:
*   If the MLflow server is unreachable (e.g., local development without a running docker container), the component logs a warning and proceeds without crashing the pipeline.
*   This allows DVC to track the stage completion locally even if centralized tracking is temporarily offline.

## Evidence of Registration
The following screenshot illustrates a successful registration run in the MLflow UI, showing the transition of metrics and the creation of version **v5** for the `ACRAS_RandomForest_v1` model.

![MLflow UI Registration](../../figures/mlflow_ui.png)

## Operational Hardening (v2.0)
The registration stage has been hardened to ensure reliable model promotion:

### 1. Standardized Logger Initialization
*   **Contextual Logging**: Previously using a global logger, the component now uses `get_logger(__name__)`. This ensures that registration events are correctly attributed to `src.components.model_registration`, enabling precise log filtering by component.

### 2. Robust Exception Management
*   **Centralized Error Handling**: Bare `except` blocks have been replaced with specific `CustomException` handlers. 
*   **Fail-Safe Connection**: Connection errors with the MLflow server are caught and logged with full traceback context. The "Gracious Fallback" is now explicitly logged as a `WARNING` or `ERROR`, ensuring that failure to register a model is visible in the structured log stream.

## Why this is "Robust MLOps"
1.  **Centralized Governance**: Pulls models by name and version from the Model Registry, removing "local file" dependencies.
2.  **Automated Versioning**: Every successful run increments the model version for a clear audit trail.
3.  **Performance Guarantees**: Quality gate prevents promotion of sub-threshold models.
4.  **Resilient Execution**: Integration of `CustomException` and structured logging ensures that registry failures are documented and diagnostically accessible.
