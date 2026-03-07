# Feature Engineering Report

## Overview
This report documents the feature engineering logic implemented in `src/features/build_features.py`. This module is responsible for transforming raw financial data into predictive features for the ACRAS model.

## 1. Architecture
*   **Module**: `src.features.build_features`
*   **Entry Point**: `engineer_features(df: pd.DataFrame) -> pd.DataFrame`
*   **Integration**: Called by `DataIngestion` component immediately after loading and merging raw data.

## 2. Implemented Transformations

### A. Column Translation
Maps raw Spanish column names to the standardized English schema to ensure code readability and maintainability.

| Raw (Spanish) | Standard (English) | Description |
| :--- | :--- | :--- |
| `riesgo_sector` | `sector_risk_score` | Risk score associated with the industry sector. |
| `anos_operando` | `years_operating` | Number of years the company has been active. |
| `crecimiento_ingresos` | `revenue_growth` | Year-over-year revenue growth rate. |
| `default_12m` | `target` | Binary target (1 = Default, 0 = No Default). |
| `pd_verdadera` | `default_probability` | The "true" probability of default from expert assessment. |

### B. Financial Ratio Calculation
Derives key financial health indicators from raw statement items.

| Feature | Formula | Business Logic |
| :--- | :--- | :--- |
| **EBITDA Margin** | `ebitda / ingresos` | Measures operating profitability as a percentage of revenue. Returns `0` if revenue is 0 to avoid division errors. |
| **Debt to Equity** | `pasivos_totales / patrimonio` | Measures financial leverage. Returns `10` (high risk cap) if equity is 0, treating it as highly leveraged. |
| **Current Ratio** | `(caja + cuentas_cobrar + inventario) / cuentas_pagar` | Proxy for liquidity. Uses generic buckets for current assets/liabilities. Returns `0` if no liabilities (or error). |

### C. Data Cleaning & Safety
*   **Infinite Values**: `np.inf` and `-np.inf` are replaced with `0` (or capped values) to prevent model training crashes.
*   **NaN Handling**: Missing values resulting from division by zero are imputed with safe defaults (`0` for margins, `10` for leverage).
*   **Type Casting**: Ensures the `target` column is strictly `int` for binary classification.

## 3. Future Improvements
*   **Advanced Imputation**: Replace constant filling (e.g., Debt-to-Equity = 10) with industry-median imputation.
*   **Outlier Capping**: Implement Winsorization for ratios to limit the effect of extreme outliers.
*   **Log Transforms**: Apply log transformation to skewed features like `ingresos` (Revenue) and `activos_totales` (Total Assets).
