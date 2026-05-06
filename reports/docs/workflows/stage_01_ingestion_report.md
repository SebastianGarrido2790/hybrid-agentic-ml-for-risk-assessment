# Stage 01: Data Ingestion & Engineering Architecture Report

## Purpose
The **Data Ingestion & Engineering Stage** is responsible for establishing the numerical foundation for the ACRAS system. Its primary goal is to integrate raw financial and risk data, perform initial feature engineering (financial ratios), and provide reproducible data splits for downstream machine learning stages.

## Workflow Logic
This stage implements a sophisticated integration logic that merges disparate data sources while preventing "Cartesian Product" explosion through strategic aggregation.

```mermaid
sequenceDiagram
    participant DS as Raw Data (data/raw)
    participant CM as Configuration Manager
    participant DI as Data Ingestion Component
    participant FE as Feature Engineer (build_features.py)
    participant AR as Artifacts Root

    DI->>CM: Request DataIngestionConfig
    CM-->>DI: typed config (paths, ratios, seed)
    
    DI->>DS: Load Raw Financials + PD Tables
    DI->>DI: Aggregate Financials (Latest Year)
    DI->>DI: Aggregate PD (Mean risk metrics)
    DI->>DI: Inner Merge on 'id_empresa'
    
    DI->>FE: Call engineer_features(merged_df)
    FE->>FE: Calculate EBITDA Margin, Debt-to-Equity, Current Ratio
    FE->>FE: Translate Columns (Spanish -> English)
    FE-->>DI: Enriched DataFrame

    DI->>DI: Perform standardized 3-Way split
    DI->>AR: Save train.csv (70%)
    DI->>AR: Save val.csv (15%)
    DI->>AR: Save test.csv (15%)
```

## Integration & Engineering Strategy

### 1. Data Aggregation
To handle companies with multiple years of data or multiple PD records:
*   **Financials**: We select only the **LATEST** record per company (based on the `ano` column) to represent the current financial health.
*   **PD Records**: We calculate the **MEAN** of numerical risk factors to obtain a smoothed probability profile per entity.

### 2. Feature Engineering (build_features.py)
We transform the raw accounting data into predictive health indicators:
*   **EBITDA Margin**: Measures operational efficiency relative to revenue.
*   **Debt-to-Equity**: Assesses financial leverage and risk.
*   **Current Ratio**: Evaluates short-term liquidity and solvency.

### 3. Translation
To ensure the codebase adheres to English MLOps standards, all raw Spanish columns (e.g., `riesgo_sector`, `p_default`) are translated into our English schema (e.g., `sector_risk_score`, `target`).

## Data Splitting Strategy
We use a **Double train_test_split** approach to achieve the specific ratios defined in `config/params.yaml`:
1.  **Split 1**: Data $\rightarrow$ `Train` and `Temp`.
    *   `Temp` size = `Val` + `Test` (e.g., 0.30).
2.  **Split 2**: `Temp` $\rightarrow$ `Validation` and `Test`.
    *   Executed using a relative ratio: `test_size / (test_size + val_size)`.

## Configuration Parameters
Managed in `config/params.yaml` under the `data_split` key:
*   `test_size`: 0.15
*   `val_size`: 0.15
*   `random_state`: 42

## Generated Artifacts
All artifacts are stored in `artifacts/data_ingestion/`:
*   `train.csv`: Training set used by the `Model Training` stage.
*   `val.csv`: Validation set used for schema check and tuning.
*   `test.csv`: Hold-out test set for final performance reporting.

## Operational Hardening (v2.0)
The ingestion stage has been hardened with "Production-Elite" observability and resilience standards:

### 1. Structured Logging
Replaced all `print()` statements with the standardized `get_logger(__name__)` utility. This allows for:
*   **Module-Level Filtering**: Logs are now tagged with `src.components.data_ingestion`.
*   **Source Tracing**: Ingestion events are captured in the `RotatingFileHandler` for long-term auditing.

### 2. Defensive Error Handling
Implemented `CustomException` with `sys` traceback capture.
*   **Missing Data Detection**: If a raw CSV file is missing or inaccessible, the system logs a high-fidelity error with the exact line number of the failure before terminating the pipeline gracefully.

### 3. Memoized Performance
Implemented `@functools.lru_cache` for the data loading helper.
*   **I/O Efficiency**: Repeated calls to the same data source (e.g., during testing or multi-step analysis) now serve from memory instead of hitting the disk, reducing overall pipeline latency.

## Why this is "Robust MLOps"
1.  **Elimination of Redundancy**: Aggregation logic ensures a strict 1:1 mapping per company, preventing data bloating and bias.
2.  **Feature Consistency**: By moving translation and ratio calculation to the Ingestion stage, we ensure all downstream stages operate on a standardized, English-only schema.
3.  **Reproducible Geometry**: Anchoring the 3-way split with a fixed `random_state` ensures that every pipeline run uses the exact same data partitions.
4.  **Production Observability**: Transitioning from `print()` to structured logging ensures that ingestion telemetry is visible to enterprise monitoring stacks.
