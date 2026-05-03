# Data Augmentation Report - Perfect Scores

**Metrics**
```json
{
    "accuracy": 1.0,
    "precision": 1.0,
    "recall": 1.0,
    "f1_score": 1.0,
    "roc_auc": 1.0
}
```

## Analysis

The "perfect" scores (1.0) are a classic symptom of **synthetic data that is too predictable**. Currently, the `synthetic_data_generator.py` creates "distressed" samples using very strict, deterministic rules (e.g., *all* synthetic samples have `default_12m = 1` and all have high debt/low EBITDA). The model is essentially just learning the hardcoded rules rather than identifying subtle patterns.

To achieve more realistic, human-like metrics (e.g., ROC AUC 0.75 - 0.85), we should implement the following "Entropy" strategies:

### 1. Introduce Class Overlap (The "Healthy-but-Risky" companies)
Generate "False Positives" in synthetic data.
*   **Action**: Create synthetic companies with distressed financials (low EBITDA, high debt) but set `default_12m = 0`.
*   **Why**: Real-world models need to see companies that look bad on paper but somehow manage to survive. This teaches the model that high leverage doesn't *always* mean default.

### 2. Probabilistic Labeling (Noise)
Instead of setting `default_12m = 1` for every synthetic sample, use a probability function.
*   **Action**: Use a sigmoid-like logic where companies with extremely high debt have a 90% chance of default, while those with moderate debt only have a 20% chance.
*   **Why**: This prevents the model from finding a "perfect" split point in the data.

### 3. Feature Correlation Noise
*   **Action**: Add random Gaussian noise to the generated financial ratios.
*   **Why**: Right now, the relationship between `ingresos` and `ebitda` is a simple linear range. Adding noise makes the features less "clean" and more like real, messy accounting data.

### 4. Remove "Target Leaks"
Check if features include values that wouldn't be known in advance.
*   **Action**: Check `src/tools/synthetic_data_generator.py`. If `pd_verdadera` (True Probability of Default) is being used as a training feature, that is a direct **data leak**. It should be removed from the training set.

---

### 🛠️ Proposed Change to the Generator:
I recommend modifying the `generate_synthetic_data` function in `src/tools/synthetic_data_generator.py` to use a **Probabilistic Default Logic**. 
