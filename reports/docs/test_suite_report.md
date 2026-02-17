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
│   ├── test_config.py
│   ├── test_data_ingestion.py
│   ├── test_data_validation.py
│   ├── test_data_transformation.py
│   └── test_model_trainer.py
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
| **Data Validation** | `test_data_validation.py` | - **Schema Validation**: Checks for presence of all required columns.<br>- **Pass Scenario**: Generates `status: True`.<br>- **Fail Scenario**: Generates `status: False` on missing columns. |
| **Data Transformation** | `test_data_transformation.py` | - **Pipeline Construction**: Verifies `ColumnTransformer` creation.<br>- **Execution**: Ensures data is transformed and artifacts (preprocessor) are saved.<br>- Correct handling of numerical vs. categorical columns. |
| **Model Trainer** | `test_model_trainer.py` | - **Training**: Verification of `RandomForestClassifier` fitting.<br>- **Persistence**: Ensures trained model is saved as `.joblib`.<br>- Hyperparameter parameter passing. |

### 3.2 Integration Tests

| Flow | Test File | Description |
| :--- | :--- | :--- |
| **Ingestion -> Validation** | `test_pipeline.py` | - **Artifact Handoff**: Verifies that files created by Ingestion (`train.csv`) are correctly located and read by Validation.<br>- **End-to-End Success**: Mocks data generation to ensure the full sequence runs without error. |

### 3.3 API Tests (Prediction Service)

| Endpoint | Test File | Scenarios Verified |
| :--- | :--- | :--- |
| **GET /health** | `test_api.py` | - Returns `200 OK` and service status.<br>- Checks if artifacts are loaded. |
| **POST /predict** | `test_api.py` | - **Low Risk**: Mocks model probability < 0.3.<br>- **High Risk**: Mocks model probability > 0.7.<br>- **Validation Error**: Returns `422 Unprocessable Content` for invalid JSON payloads. |
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
tests\app\test_api.py .....
tests\integration\test_pipeline.py .
tests\unit\test_config.py .
tests\unit\test_data_ingestion.py ..
tests\unit\test_data_transformation.py ..
tests\unit\test_data_validation.py ..
tests\unit\test_model_trainer.py .

================== 14 passed in 2.51s ==================
```

### Dependencies
- `pytest`: Core framework.
- `unittest.mock`: For isolation (mocking filesystem, external calls, and ML models).
- `httpx` / `fastapi.testclient`: For API testing.

## 5. Recent Improvements
- **Docstrings**: All test modules are now fully documented with distinct purpose headers.
- **Deprecation Fixes**: Updated API tests to use modern `HTTP_422_UNPROCESSABLE_CONTENT` status codes.
- **Cleanup**: Removed unused imports across the suite.

## 6. Coverage Goals
Current tests cover the critical path of the application. Future work will focus on:
- Adding `pytest-cov` for quantitative coverage metrics.
- Expanding integration tests to cover the Model Training handoff.
