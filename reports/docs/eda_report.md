# Exploratory Data Analysis Report

## Overview
This report summarizes the findings from the **Industrialized EDA** pipeline applied to the real ACRAS financial dataset.

## Dataset Characteristics
*   **Total Companies**: 500 (merged from training and validation raw sources).
*   **Source**: Raw financial statements and Probability of Default (PD) records.
*   **Composition**: Purely financial/risk indicators (No synthetic text).

## Key Findings

### 1. Financial Health Indicators
*   **EBITDA Margin**: Distribution shows the operational profitability. Outliers have been capped/handled.
*   **Debt-to-Equity**: Indicates leverage. High values suggest higher risk, which correlates with the default target.
*   **Current Ratio**: Measures liquidity. Lower ratios are generally observed in defaulting companies.

### 2. Risk Metrics
*   **Sector Risk Score**: Quantifies the inherent risk of the industry.
*   **Default Probability (PD)**: The raw PD values provided in the dataset show a strong correlation with the binary `target`, verifying their predictive power.

### 3. Data Integrity
*   **Unique ID constraint**: The aggregation strategy (Latest Financials + Mean PD) successfully produced a 1:1 company-to-record mapping, eliminating Cartesian products.
*   **Missing Values**: Handled via imputation (e.g., 0 for calculating ratios with zero denominators) and safe division.

## Data Schema (English)
The following columns are now standard in the processed dataset:
*   `sector_risk_score` (was `riesgo_sector`)
*   `years_operating` (was `anos_operando`)
*   `revenue_growth` (was `crecimiento_ingresos`)
*   `target` (was `default_12m`)
*   `default_probability` (was `pd_verdadera`)
*   Calculated: `ebitda_margin`, `debt_to_equity`, `current_ratio`.

## Recommendations for Modeling
1.  **Feature Scaling**: Given the wide range of financial values (Revenue vs Ratios), robust scaling (e.g., `RobustScaler`) is recommended.
2.  **Imbalance**: Check the ratio of `target=1` vs `target=0`. If highly imbalanced, consider SMOTE or class weighting.
3.  **Non-Linearity**: Financial ratios often have non-linear relationships with default risk; tree-based models (XGBoost/LightGBM) are likely to perform better than linear regression.
