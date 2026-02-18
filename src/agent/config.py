"""
Configuration settings for the Agentic Reasoning Engine.

This module defines the `AgentSettings` class, which loads configuration variables
(API keys, model names, API URLs) from environment variables using Pydantic Settings.
"""

from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """Configuration for the Agentic Layer"""

    # LLM Settings
    GOOGLE_API_KEY: Optional[str] = None
    HUGGINGFACEHUB_API_TOKEN: Optional[str] = None

    # Model Names
    GEMINI_MODEL: str = "gemini-1.5-flash"
    HF_MODEL: str = "meta-llama/Meta-Llama-3-8B-Instruct"

    # API Settings
    ML_API_URL: str = "http://localhost:8000/predict"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache()
def get_agent_settings() -> AgentSettings:
    """Return cached settings"""
    return AgentSettings()
