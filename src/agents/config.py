"""
Configuration settings for the Agentic Reasoning Engine.

This module defines the `AgentSettings` class, which loads configuration variables
(API keys, model names, API URLs) from environment variables using Pydantic Settings.
"""

from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """Configuration for the Agentic Layer"""

    # LLM Settings
    GOOGLE_API_KEY: Optional[str] = None
    HUGGINGFACEHUB_API_TOKEN: Optional[str] = None
    DEFAULT_LLM_PROVIDER: Literal["gemini", "huggingface"] = "gemini"

    # Model Names
    HF_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"  # Tier 1/2 Performance (7B is more reliable for Free API)
    GEMINI_POWER_MODEL: str = "gemini-1.5-flash"  # Tier 1/2 Performance
    GEMINI_LITE_MODEL: str = (
        "gemini-2.5-flash-lite"  # Standardized for high availability
    )

    # API Settings
    ML_API_URL: str = "http://localhost:8000/predict"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


def get_agent_settings() -> AgentSettings:
    """Return settings (no cache to support hot-reloading)"""
    return AgentSettings()
