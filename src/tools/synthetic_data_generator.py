import pandas as pd
import numpy as np
import os


def generate_synthetic_data(n_samples=50):
    """
    Generates synthetic data for distressed companies (defaults).
    """
    np.random.seed(42)

    # Starting ID after the last real one (assumed 450)
    start_id = 1000

    # Financials
    ids = np.arange(start_id, start_id + n_samples)
    years = np.random.choice([2023, 2024], size=n_samples)

    # Distressed Logic:
    # Low/Negative EBITDA
    ingresos = np.random.uniform(500000, 2000000, n_samples)
    ebitda = ingresos * np.random.uniform(
        -0.15, 0.05, n_samples
    )  # mostly negative to low positive margin

    # High Debt (DE > 2)
    patrimonio = ingresos * np.random.uniform(0.1, 0.3, n_samples)
    pasivos = patrimonio * np.random.uniform(2.0, 5.0, n_samples)
    activos = pasivos + patrimonio

    # Low Liquidity
    cuentas_pagar = pasivos * 0.4
    quick_assets = cuentas_pagar * np.random.uniform(
        0.5, 0.9, n_samples
    )  # Current ratio < 0.9
    caja = quick_assets * 0.2
    cuentas_cobrar = quick_assets * 0.4
    inventario = quick_assets * 0.4

    # Other
    gastos_intereses = pasivos * 0.08

    financials = pd.DataFrame(
        {
            "id_empresa": ids,
            "ano": years,
            "ingresos": ingresos,
            "ebitda": ebitda,
            "activos_totales": activos,
            "pasivos_totales": pasivos,
            "patrimonio": patrimonio,
            "caja": caja,
            "gastos_intereses": gastos_intereses,
            "cuentas_cobrar": cuentas_cobrar,
            "inventario": inventario,
            "cuentas_pagar": cuentas_pagar,
        }
    )

    # PD Table
    # High risk indicators
    pd_table = pd.DataFrame(
        {
            "id_empresa": ids,
            "riesgo_sector": np.random.uniform(3.0, 5.0, n_samples),  # High risk sector
            "anos_operando": np.random.randint(1, 5, n_samples),  # Young companies
            "ratio_mora": np.random.uniform(0.1, 0.4, n_samples),  # High delinquency
            "ratio_utilizacion": np.random.uniform(
                0.8, 1.0, n_samples
            ),  # Maxed out credit lines
            "crecimiento_ventas": np.random.uniform(
                -0.2, 0.0, n_samples
            ),  # Shrinking sales
            "margen_beneficio": ebitda / ingresos,  # Consistent with financials
            "score_buro": np.random.randint(300, 550, n_samples),  # Low bureau score
            "default_12m": 1,  # TARGET = 1
            "pd_verdadera": np.random.uniform(0.15, 0.50, n_samples),  # High PD
        }
    )

    return financials, pd_table


if __name__ == "__main__":
    # Check paths - assuming run from project root
    fin_path = "data/raw/financial_statements_training.csv"
    pd_path = "data/raw/pd_training.csv"

    if os.path.exists(fin_path) and os.path.exists(pd_path):
        print("Generating synthetic data...")
        syn_fin, syn_pd = generate_synthetic_data(50)

        print(f"Appending to {fin_path} and {pd_path}...")

        # Append mode (header=False if file exists)
        syn_fin.to_csv(fin_path, mode="a", header=False, index=False)
        syn_pd.to_csv(pd_path, mode="a", header=False, index=False)

        print("Success! Added 50 positive samples.")
    else:
        print("Error: Raw data files not found. Are you running from project root?")
