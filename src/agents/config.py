"""
Configuration settings for the Agentic Reasoning Engine.

This module defines the `AgentSettings` class, which loads configuration variables
(API keys, model names, API URLs) from environment variables using Pydantic Settings.
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """Configuration for the Agentic Layer"""

    # LLM Settings
    GOOGLE_API_KEY: str | None = None
    HUGGINGFACEHUB_API_TOKEN: str | None = None
    DEFAULT_LLM_PROVIDER: Literal["gemini", "huggingface"] = "gemini"

    # Model Names
    HF_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"  # Tier 1/2 Performance (7B is more reliable for Free API)
    GEMINI_POWER_MODEL: str = "gemini-2.5-flash"  # Tier 1/2 Performance
    GEMINI_LITE_MODEL: str = (
        "gemini-2.5-flash-lite"  # Standardized for high availability
    )

    # API Settings
    ML_API_URL: str = "http://localhost:8000/v1/predict"

    # Project Settings
    PROJECT_NAME: str = "ACRAS"
    LOG_LEVEL: str = "INFO"
    ENV: str = "local"

    # MLflow Settings
    MLFLOW_TRACKING_URI: str | None = None

    # Telemetry Settings
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4318"
    DEBUG_TELEMETRY: int = 0

    # Evaluation Settings
    LOG_EVALS_TO_MLFLOW: int = 0

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="forbid"
    )


def get_agent_settings() -> AgentSettings:
    """Return settings (no cache to support hot-reloading)"""
    return AgentSettings()
