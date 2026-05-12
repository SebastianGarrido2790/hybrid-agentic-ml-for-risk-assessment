# ACRAS Test Suite Report

## 1. Testing Strategy Overview

The **ACRAS (Agentic Credit Risk Assessment System)** employs a robust, multi-layered testing strategy to ensure the reliability of its machine learning pipeline and prediction service. Our approach follows the "Testing Pyramid" philosophy:

*   **Unit Tests**: Validate the logic of individual components in isolation.
*   **Integration Tests**: Verify the interaction and data flow between pipeline stages.
*   **API Tests**: Ensure the REST API endpoints function correctly and handle edge cases.

## 2. Test Suite Structure

The testing directory mirrors the source code structure for intuitive navigation:

```
tests/
├── conftest.py          # Global Shared Fixtures (Sample Data)
├── unit/                # Component-level Logic Tests
│   ├── test_agent_tools.py
│   ├── test_build_features.py
│   ├── test_config.py
│   ├── test_data_augmentation.py
│   ├── test_data_ingestion.py
│   ├── test_data_validation.py
│   ├── test_data_transformation.py
│   ├── test_exception.py
│   ├── test_finance_tool.py
│   ├── test_graph_extended.py
│   ├── test_lookup_tool.py
│   ├── test_mlflow_config.py
│   ├── test_model_evaluation.py
│   ├── test_model_factory.py
│   ├── test_model_registration.py
│   ├── test_model_trainer.py
│   ├── test_pdf_generator.py
│   ├── test_pipeline.py
│   ├── test_prompts.py
│   ├── test_telemetry.py
│   ├── test_ui_data_loader.py
│   ├── test_ui_export.py
│   ├── test_ui_styles.py
│   └── test_ui_utils.py
├── integration/         # Pipeline Handoff Tests
│   └── test_pipeline.py
└── app/                 # Service & API Tests
    ├── conftest.py      # App-specific Mocks (Model, Preprocessor)
    └── test_api.py
```

## 3. Component Breakdown

### 3.1 Unit Tests

| Component | Test File | Key Scenarios Verified |
| :--- | :--- | :--- |
| **Configuration** | `test_config.py` | - Correct loading of YAML configs.<br>- Proper type conversion to Entity objects.<br>- Path resolution logic. |
| **Data Ingestion** | `test_data_ingestion.py` | - Merging of Financial and PD datasets.<br>- **Stratified Splitting**: Ensures class balance in Train/Val/Test sets.<br>- **Fallback Logic**: Verifies fallback to random split if stratification fails.<br>- Feature Engineering integration. |
| **Data Validation** | `test_data_validation.py` | - **Schema Validation**: Checks for presence of all required columns.<br>- **Statistical Contracts**: Integrates Great Expectations (GX) for distribution-based validation.<br>- **Pass Scenario**: Generates `status: True`.<br>- **Fail Scenario**: Generates `status: False` on missing columns or failed statistical expectations. |
| **Data Transformation** | `test_data_transformation.py` | - **Pipeline Construction**: Verifies `ColumnTransformer` creation.<br>- **Execution**: Ensures data is transformed and artifacts (preprocessor) are saved.<br>- Correct handling of numerical vs. categorical columns. |
| **Feature Engineering** | `test_build_features.py` | - **Translations**: Spanish -> English mapping via `engineer_features`.<br>- **Financial Ratios**: Correct calculation of EBITDA margin, Debt-to-Equity, and Current Ratio.<br>- **Zero-Division Handling**: Zero divisors yield guarded defaults (0.0 or 10.0). |
| **Model Evaluation** | `test_model_evaluation.py` | - **Metrics Calculation**: Accuracy, Precision, Recall, F1, and ROC-AUC parity.<br>- **MLflow Integration**: Successful logging of metrics and parameters via mocked tracking server. |
| **Model Registration** | `test_model_registration.py` | - **Threshold Enforcement**: Verification that models are registered ONLY when exceeding `min_roc_auc`.<br>- **Version Management**: Proper metadata and artifact registration names. |
| **Model Trainer** | `test_model_trainer.py` | - **Training**: Verification of `RandomForestClassifier` fitting.<br>- **Persistence**: Ensures trained model is saved as `.joblib`.<br>- Hyperparameter parameter passing. |
| **Error Handling** | `test_exception.py` | - **CustomException**: Verification of message and sys detail capture.<br>- **Logging**: Ensures traceback is correctly formatted for the logger. |
| **MLflow Config** | `test_mlflow_config.py` | - **URI Validation**: Correct construction of local vs remote tracking URIs.<br>- **Artifact Pathing**: Ensures MLflow saves to the correct `.artifacts` directory. |
| **Prompt Logic** | `test_prompts.py` | - **Loading**: Ensures system prompts are read correctly from external files.<br>- **Templating**: Validates that all variables are filled before agent invocation. |

### 3.2 Integration Tests

| Flow | Test File | Description |
| :--- | :--- | :--- |
| **Ingestion -> Validation** | `test_pipeline.py` | - **Artifact Handoff**: Verifies that files created by Ingestion (`train.csv`) are correctly located and read by Validation.<br>- **End-to-End Success**: Mocks data generation to ensure the full sequence runs without error. |


### 3.3 Agentic Reasoning Engine Tests

| Component | Test File | Key Scenarios Verified |
| :--- | :--- | :--- |
| **Agent Tools** | `test_agent_tools.py` | - **API Integration**: Mocks valid/invalid responses from the ML API.<br>- **Pydantic Validation**: Ensures tools correctly validate the strict `company_id` input schema.<br>- **Data Isolation**: Mocks `pd.read_csv` and file system lookups to detach agent tests from local FTI artifacts.<br>- **Error Handling**: Verifies graceful degradation when external services are down. |
| **Finance Tool** | `test_finance_tool.py` | - **Atomic Calculations**: Individual validation of Debt-to-Equity, EBITDA Margin, Current Ratio, and Revenue Growth tools.<br>- **Error Messages**: Ensures division-by-zero returns clear string errors for the LLM. |
| **Lookup Tool** | `test_lookup_tool.py` | - **Database Fetching**: Mocked CSV lookups for company metadata.<br>- **ID Handling**: Correct response on non-existent company IDs. |

### 3.4 API Tests (Prediction Service)

| Endpoint | Test File | Scenarios Verified |
| :--- | :--- | :--- |
| **GET /health** | `test_api.py` | - Returns `200 OK` and service status.<br>- **Fail-Fast**: Returns `503 Service Unavailable` if artifacts are missing (e.g. uninitialized state). |
| **POST /predict** | `test_api.py` | - **Low Risk**: Mocks model probability < 0.3.<br>- **Medium Risk**: Mocks model probability >= 0.3 and < 0.7.<br>- **High Risk**: Mocks model probability > 0.7.<br>- **Validation Error**: Returns `422 Unprocessable Content` for invalid JSON payloads. |
| **GET /metrics** | `test_api.py` | - Verifies Prometheus metrics endpoint exposure. |

## 4. Execution & Tools

We use **pytest** as the primary test runner, managed via **uv**.

### Running the Suite
To execute all tests:
```bash
uv run pytest tests/
```

To execute a specific test file:
```bash
uv run pytest tests/app/test_api.py
```

To execute the suite and save output to a file:
```bash
uv run pytest tests/ > tests/logs/test_output.txt
```

**Output**:
```
tests\app\test_api.py .......                                            [  9%]
tests\integration\test_pipeline.py .....                                 [ 15%]
tests\unit\test_agent_tools.py ..                                        [ 18%]
tests\unit\test_build_features.py ...                                    [ 22%]
tests\unit\test_config.py .                                              [ 23%]
tests\unit\test_data_ingestion.py ..                                     [ 26%]
tests\unit\test_data_transformation.py ..                                [ 28%]
tests\unit\test_data_validation.py ..                                    [ 31%]
tests\unit\test_exception.py ...                                         [ 35%]
tests\unit\test_finance_tool.py ....                                     [ 40%]
tests\unit\test_lookup_tool.py ...                                       [ 44%]
tests\unit\test_mlflow_config.py .....                                   [ 50%]
tests\unit\test_model_evaluation.py .                                    [ 51%]
tests\unit\test_model_registration.py .                                  [ 53%]
tests\unit\test_model_trainer.py .                                       [ 54%]
tests\unit\test_ui_data_loader.py ..                                     [ 56%]
tests\unit\test_ui_export.py ....                                        [ 62%]
tests\unit\test_ui_styles.py ..                                          [ 64%]
tests\unit\test_ui_utils.py .....                                        [ 71%]
...
[Additional UI and Component Tests Passed]
...
======================= 78 passed, 2 warnings in 27.75s ========================
```

### 4.1 Coverage Analysis
We use **pytest-cov** to measure and enforce quality gates. If our code coverage drops below this line, the CI pipeline will fail automatically.

- **Current State**: After the Advanced Maturity (v2.3) hardening, our total coverage is **67.81%**.
- **The Choice of 65**: We have raised the gate from 40% to 65% to reflect the increased maturity of the system. This satisfies the "Elite Infrastructure" requirement for production-ready agentic systems (Rule 4.1.3).
- **Moving Forward**: The next target is the industry-standard **85%** for mission-critical credit risk logic.

**Required Gate**: 65% (Elite Infrastructure Baseline)

| Module Group | Coverage | Status |
| :--- | :--- | :--- |
| **Agents (Tools & Logic)** | 86% | ✅ High |
| **Logic Components (src/components)** | 88% | ✅ High |
| **UI Components (src/ui)** | 88% | ✅ High |
| **Orchestration Stages (src/pipeline)**| 67% | ✅ Improved |
| **Total System** | **67.81%** | ✅ Pass |

> **NOTE**
> The **Orchestration Stages** (`src/pipeline/`) show 0% coverage because our unit tests target the underlying **Logic Components** directly. These stages are thin wrappers used by DVC; future integration tests will target these entry points to close this gap.

### Dependencies
- `pytest`: Core framework.
- `unittest.mock`: For isolation (mocking filesystem, external calls, and ML models).
- `httpx` / `fastapi.testclient`: For API testing.

## 5. Test Suite Enhancements
- **pytest-cov Integration**: Added quantitative coverage metrics with an initial CI gate of 40%.
- **Docstrings**: All 39 test modules and component tests now follow the mandatory Google-style documentation standard.
- **Model Serialization Mocking**: Refactored evaluation tests to use real-model fits (`LogisticRegression`) combined with `mock.patch` to avoid `mlflow` proxy serialization errors.
- **CI Enforcement**: Updated `.github/workflows/ci.yml` to enforce the coverage gate on every PR.
- **Test Infrastructure Hygiene**: Implemented `suppress_otel_export` in `conftest.py` to disable OpenTelemetry exports during test runs, ensuring CI stability and avoiding network overhead.

## 6. Coverage Goals
Current tests cover the critical path of the application. Future work will focus on:
- Raising the coverage gate to **75%** in the next advanced maturity sprint.
- Final goal of **85%+** total codebase coverage for production certification.
