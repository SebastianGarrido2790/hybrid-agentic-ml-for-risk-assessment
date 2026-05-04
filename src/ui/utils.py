"""
Utility functions for the ACRAS UI, including risk score extraction.
"""

import re


def extract_risk_score(text: str) -> float:
    """
    Extracts the final risk score from agent-generated text.

    Takes the LAST occurrence of 'Risk Score' to avoid picking up
    intermediate mentions of 'Bureau Score' or other metrics.

    Args:
        text: The raw text output from the orchestrator agent.

    Returns:
        float: The extracted risk score (0-100). Defaults to 50.0 if not found.
    """
    # Look for the specific system tag first, then fallback to general matches
    system_tag_match = re.search(
        r"SYSTEM FINAL RISK SCORE:\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE
    )
    if system_tag_match:
        score = float(system_tag_match.group(1))
        # Handle cases where model spits out 725 instead of 7.25
        if score > 100:
            score = score / 100
        return min(max(score, 0.0), 100.0)

    # Fallback to last occurrence of 'Score'
    matches = re.findall(
        r"(?:Risk\s+)?Score:\*{0,2}\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE
    )
    if matches:
        score = float(matches[-1])
        # Handle cases where score might be a probability (0-1)
        if score <= 1.0 and "PD" in text:
            score *= 100
        return min(max(score, 0.0), 100.0)  # Clamp to 0-100
    return 50.0
