# ML Model Training Assessment

Based on the project constraints (Tabular Financial Data, Small Dataset $N=500$, Explainability Requirement) and the architectural documents, here is the assessment of five candidate models for the ACRAS baseline.

---

### **Candidate Assessment**

We evaluate these candidates based on the **ACRAS** requirements: handling non-linear financial ratios, dataset size, and explainability for the Risk Manager persona.

#### **1. Logistic Regression (The "Sanity Check")**

* **Mechanism:** Linear decision boundary using a sigmoid activation: .
* **Pros:** Highly interpretable (coefficients = feature impact); extremely fast training; virtually impossible to overfit if regularized ().
* **Cons:** **Fatal flaw for ACRAS:** Cannot capture non-linear relationships (e.g., the "U-shaped" risk of rapid growth vs. stagnation) without manual feature engineering (polynomial terms).
* **Verdict:** **Reject as Primary Baseline.** Use only as a "floor" to ensure the complex models are actually learning.

#### **2. Random Forest (Stable & Interpretable)**

* **Mechanism:** Bagging (Bootstrap Aggregating) ensemble of decorrelated Decision Trees.
* **Pros:** * **Non-Linearity:** Natively captures complex interactions between ratios (e.g., High Debt is okay *only if* EBITDA is high).
* **Robustness:** Averaging multiple trees reduces variance, making it very stable on small datasets like yours ().
* **No Scaling Required:** Technically invariant to feature scaling (though your pipeline includes it, which is fine).
* **Cons:** Slower inference than Logistic Regression (must traverse ); large memory footprint if trees are deep.
* **Verdict:** **Select.** It works well with default hyperparameters, setting a high bar for future optimization.

#### **3. XGBoost (The "Performance" Challenger)**

* **Mechanism:** Gradient Boosting framework that builds trees sequentially to correct the errors of previous trees.
* **Pros:** State-of-the-art performance for tabular data; handles missing values internally (though your pipeline imputes them); regularization parameters () prevent overfitting.
* **Cons:** **High complexity.** Requires careful tuning of learning rate (), tree depth, and stopping criteria. On small data (), it is prone to overfitting if the tree depth is not strictly constrained.
* **Verdict:** **Reserve for Phase 2.** Use this to try and beat the Random Forest baseline once the pipeline is stable.

#### **4. Support Vector Machine (SVM - RBF Kernel)**

* **Mechanism:** Finds the hyperplane that maximizes the margin between classes, projected into high-dimensional space via the Radial Basis Function kernel.
* **Pros:** Effective in high-dimensional spaces; robust when classes are separable.
* **Cons:** **Black Box.** Harder to interpret "why" a specific company was rejected (no direct feature importance). Extremely sensitive to hyperparameter  and . Computationally expensive () if the dataset grows significantly.
* **Verdict:** **Reject.** Lacks the transparency required for the "Financial Analyst" agent to generate qualitative insights.

#### **5. Multi-Layer Perceptron (MLP / Neural Network)**

* **Mechanism:** Feed-forward neural network with non-linear activation functions (ReLU).
* **Pros:** Can model infinitely complex functions (Universal Approximation Theorem).
* **Cons:** **Data Hungry.** With only 500 data points, a neural network will likely memorize the training set (overfit) rather than generalize. It is also a complete "black box."
* **Verdict:** **Reject.** Overkill and statistically dangerous for this dataset size.

---

### **The Verdict: Random Forest Classifier**

**Random Forest** is the optimal choice for your **robust baseline**. While XGBoost may eventually offer marginally higher performance (AUC) after heavy tuning, Random Forest provides the best balance of "out-of-the-box" stability, resistance to overfitting on small datasets ($N=500$), and feature importance interpretability—critical for the "Reasoning Engine" agents.