"""
Active Prompt Registry and Version Configuration for ACRAS Agents.

This module acts as the 'Brain' for prompt management. It serves as a
centralized registry that maps versioned external files to the constant
names used by the agents.

By centralizing the 'What' (which version is active), this module enables:
1. Version Promotion/Rollback: Change a filename here to update the system.
2. Hot-Swapping: Supports importlib.reload() in graph.py for runtime tuning.
3. Stakeholder Review: Decouples linguistic content from execution logic.
"""

from src.agents.prompt_loader import get_prompt

# --- System Prompts Registration ---
# We use versioned filenames to allow for safe promotions and rollbacks.

FINANCIAL_ANALYST_SYSTEM_PROMPT = get_prompt(
    "system_prompts", "financial_analyst_v1.txt"
)

DATA_SCIENTIST_SYSTEM_PROMPT = get_prompt("system_prompts", "data_scientist_v1.txt")

ORCHESTRATOR_SYSTEM_PROMPT = get_prompt("system_prompts", "orchestrator_v1.txt")
