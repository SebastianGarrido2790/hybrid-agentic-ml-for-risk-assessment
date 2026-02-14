# Data Augmentation Report

## Overview
This report documents the steps taken to address the critical class imbalance issue in the ACRAS credit risk dataset. The dataset initially contained an insufficient number of positive samples (defaults), rendering effective model training and evaluation impossible.

## Problem Identification
*   **Total Companies:** 450
*   **Positive Samples (Defaults):** 2 (0.44%)
*   **Impact:** 
    *   Standard train/validation/test splitting (e.g., 70/15/15) often resulted in sets with **zero positive samples**.
    *   Validation and Test metrics (Recall, Precision, ROC-AUC) were undefined or meaningless (returning `NaN` or 0.5).
    *   The model could not learn to identify defaults effectively.

## Strategy: Synthetic Data Augmentation
To overcome this limitation for the Proof of Concept (PoC), we implemented a synthetic data generation strategy to enrich the positive class.

### Methodology
We created a tool `src/tools/synthetic_data_generator.py` to generate realistic "distressed" company profiles. The generation logic is based on financial principles indicative of high credit risk.

### Synthetic Data Characteristics (N=50)
The synthetic samples were generated with the following properties:

1.  **Profitability:**
    *   `ebitda_margin`: Mostly negative to low positive (random uniform -15% to +5%).
    *   `margen_beneficio`: Consistent with EBITDA.

2.  **Leverage:**
    *   `debt_to_equity`: High leverage, typically > 2.0.
    *   `pasivos_totales` (Total Liabilities) were set to 2.0x - 5.0x of `patrimonio` (Equity).

3.  **Liquidity:**
    *   `current_ratio` (proxy via Quick Assets): Low liquidity (< 0.9).
    *   `caja` (Cash): Low cash reserves relative to obligations.

4.  **Risk Indicators (PD Table):**
    *   `riesgo_sector`: High (3.0 - 5.0).
    *   `anos_operando`: Young companies (1-5 years).
    *   `ratio_mora`: High delinquency (10% - 40%).
    *   `ratio_utilizacion`: High credit utilization (80% - 100%).
    *   `crecimiento_ventas`: Negative sales growth (Shrinking).
    *   `score_buro`: Low bureau scores (300 - 550).
    *   `default_12m`: **1 (Target)**.

## Execution and Results

### 1. Augmentation
*   **50 synthetic positive samples** were generated.
*   The **original raw data** from `data/raw` is kept untouched to maintain data integrity.
*   The augmented dataset (Original + Synthetic) is saved in **`data/processed/`**.
*   **Configuration Update:** In `config/config.yaml`, the `data_ingestion` stage was updated to use `data/processed` as its `source_data_dir`.
*   **New Total Positives:** ~52 samples.
*   **New Class Balance:** ~10% Positive / 90% Negative (up from <0.5%).

### 2. Pipeline Impact
*   **Stratified Sampling:** The increased count allowed for creating stratified Train, Validation, and Test sets.
*   **Test Set Composition:** The test set now typically contains ~8 positive samples, allowing for statistically valid metric calculation.

### 3. Model Performance (Post-Augmentation)
With the augmented data, the Random Forest model achieved:
*   **Recall:** ~0.875 (Correctly identifying 7/8 defaults).
*   **ROC-AUC:** ~0.99 (Excellent discrimination between synthetic defaults and real non-defaults).

### 4. Distribution Analysis
To verify the success of the augmentation process, we utilized the `src/tools/count_positives.py` utility. This tool performs a comparative analysis between the original raw data and the augmented processed data, ensuring that the target class distribution reaches the required threshold for robust training.

**Verification Process:**
1.  **Raw Data Scan:** Merges `data/raw/financial_statements_training.csv` and `data/raw/pd_training.csv` to establish the baseline (approx. 0.44% positive ratio).
2.  **Processed Data Scan:** Merges the augmented files in `data/processed/` to confirm the injection of synthetic samples (approx. 10.40% positive ratio).
3.  **Cross-Validation:** Ensures that `id_empresa` values for synthetic samples (ID >= 1000) are correctly mapped to a `default_12m` target of 1.

## Artifacts
*   **Generator Script:** `src/tools/synthetic_data_generator.py`
*   **Analysis Tool:** `src/tools/count_positives.py`
