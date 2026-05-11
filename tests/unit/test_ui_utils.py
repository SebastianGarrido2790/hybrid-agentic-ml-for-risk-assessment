"""
Unit tests for UI utility functions.
"""

from src.ui.utils import extract_risk_score


def test_extract_risk_score_system_tag():
    """Test extraction from SYSTEM FINAL RISK SCORE tag."""
    text = "Blah blah SYSTEM FINAL RISK SCORE: 75.5 more text"
    assert extract_risk_score(text) == 75.5


def test_extract_risk_score_fallback():
    """Test extraction from general 'Score:' fallback."""
    text = "Intermediate score: 10.0\nFinal Risk Score: 82.3"
    assert extract_risk_score(text) == 82.3


def test_extract_risk_score_scaling():
    """Test scaling of scores > 100."""
    text = "SYSTEM FINAL RISK SCORE: 725"
    assert extract_risk_score(text) == 7.25


def test_extract_risk_score_pd_scaling():
    """Test scaling of PD-like scores."""
    text = "The PD is 0.15. Final Score: 0.15"
    assert extract_risk_score(text) == 15.0


def test_extract_risk_score_not_found():
    """Test default value when no score is found."""
    text = "No score here."
    assert extract_risk_score(text) == 50.0
