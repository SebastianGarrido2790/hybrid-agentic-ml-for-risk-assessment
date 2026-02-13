import pandas as pd
import numpy as np

# Load raw data
try:
    df_fin = pd.read_csv("data/raw/financial_statements_training.csv")
    df_pd = pd.read_csv("data/raw/pd_training.csv")

    # Merge logic
    df_fin_latest = df_fin.sort_values(
        ["id_empresa", "ano"], ascending=[True, False]
    ).drop_duplicates(subset=["id_empresa"], keep="first")

    numeric_cols = df_pd.select_dtypes(include=[np.number]).columns.tolist()
    if "id_empresa" in numeric_cols:
        numeric_cols.remove("id_empresa")

    df_pd_agg = df_pd.groupby("id_empresa")[numeric_cols].mean().reset_index()

    merged = pd.merge(df_fin_latest, df_pd_agg, on="id_empresa")

    print(f"Total Unique Companies: {len(merged)}")
    print(f"Total Positive Samples (default_12m=1): {merged['default_12m'].sum()}")
    print(
        f"Positive Sample IDs: {merged[merged['default_12m'] == 1]['id_empresa'].tolist()}"
    )

except Exception as e:
    print(e)
