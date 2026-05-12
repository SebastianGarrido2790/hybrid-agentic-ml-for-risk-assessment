"""
Unified prompt loading utility for the ACRAS Agent Cluster.

This module acts as the 'Brawn' for prompt management. It provides the
deterministic logic required to resolve paths and read external text files
from the src/agents/prompts/ directory.

Following the rule of not using naked prompts, this utility decouples raw linguistic
content from Python logic, allowing for cleaner versioning and auditability.
"""

from pathlib import Path

# Base directory for all prompts
PROMPTS_ROOT = Path(__file__).parent / "prompts"


def get_prompt(category: str, filename: str) -> str:
    """Load a prompt file from the standard prompts directory.

    Args:
        category: Subdirectory (e.g., 'system_prompts')
        filename: Specific versioned file (e.g., 'financial_analyst_v1.txt')

    Returns:
        The content of the prompt file as a string.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    prompt_path = PROMPTS_ROOT / category / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8").strip()
