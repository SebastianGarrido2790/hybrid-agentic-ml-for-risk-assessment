from src.agents.prompts import (
    FINANCIAL_ANALYST_SYSTEM_PROMPT,
    DATA_SCIENTIST_SYSTEM_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
)


def test_prompts_integrity():
    """Verify that system prompts are defined and contain expected keywords."""
    assert "Senior Financial Analyst" in FINANCIAL_ANALYST_SYSTEM_PROMPT
    assert "Data Scientist" in DATA_SCIENTIST_SYSTEM_PROMPT
    assert "Chief Risk Officer" in ORCHESTRATOR_SYSTEM_PROMPT
    assert "Mora Ratio" in FINANCIAL_ANALYST_SYSTEM_PROMPT
    assert "PD (Probability of Default)" in DATA_SCIENTIST_SYSTEM_PROMPT
    assert "Final Directive" in ORCHESTRATOR_SYSTEM_PROMPT
