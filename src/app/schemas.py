"""
Data Schemas for the Prediction Service.

This module defines Pydantic models to strictly enforce data contracts
for API inputs and outputs. It ensures that the model receives data in the
expected format and types, rejecting invalid requests before they reach the inference logic.
"""

from pydantic import BaseModel, Field


class PredictionInput(BaseModel):
    """
    Schema for the model input features.
    Ensures strict type validation before data reaches the model.
    """

    ingresos: float = Field(..., description="Annual Revenue")
    ebitda: float = Field(
        ...,
        description="Earnings Before Interest, Taxes, Depreciation, and Amortization",
    )
    activos_totales: float = Field(..., description="Total Assets")
    pasivos_totales: float = Field(..., description="Total Liabilities")
    patrimonio: float = Field(..., description="Total Equity")
    caja: float = Field(..., description="Cash and Equivalents")
    gastos_intereses: float = Field(..., description="Interest Expenses")
    cuentas_cobrar: float = Field(..., description="Accounts Receivable")
    inventario: float = Field(..., description="Inventory")
    cuentas_pagar: float = Field(..., description="Accounts Payable")
    sector_risk_score: float = Field(..., description="Sector specific risk score")
    years_operating: int = Field(..., description="Number of years in operation")
    ratio_mora: float = Field(..., description="Delinquency ratio")
    ratio_utilizacion: float = Field(..., description="Credit utilization ratio")
    revenue_growth: float = Field(..., description="Year-over-year revenue growth")
    margen_beneficio: float = Field(..., description="Profit Margin")
    score_buro: float = Field(..., description="Bureau Credit Score")

    ebitda_margin: float = Field(..., description="EBITDA / Revenue")
    debt_to_equity: float = Field(..., description="Total Liabilities / Total Equity")
    current_ratio: float = Field(
        ..., description="Current Assets / Current Liabilities"
    )


class PredictionOutput(BaseModel):
    """
    Schema for the model prediction output.
    Standardizes the response format for downstream agents.
    """

    prediction: int = Field(
        ..., description="Predicted class (0: Non-Default, 1: Default)"
    )
    probability: float = Field(..., description="Probability of Default (0.0 to 1.0)")
    risk_level: str = Field(
        ..., description="Interpreted risk level: Low, Medium, High"
    )
