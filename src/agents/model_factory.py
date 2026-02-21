"""
LLM Factory for the Agentic Reasoning Engine.

This module provides a factory function `get_llm` to instantiate and configure
Large Language Models (LLMs) from different providers (Google Gemini or Hugging Face)
abstracting the initialization complexity from the rest of the application.
"""

from typing import Literal, Optional
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from src.agents.config import get_agent_settings
import logging

# Configure logger
logger = logging.getLogger(__name__)

settings = get_agent_settings()


def get_llm(
    provider: Optional[Literal["gemini", "huggingface"]] = None,
    model_name: Optional[str] = None,
) -> BaseChatModel:
    """
    Factory to return the configured LLM based on the provider.

    Args:
        provider: 'gemini' or 'huggingface'. Defaults to DEFAULT_LLM_PROVIDER from settings.
        model_name: Optional override for the model name defined in settings.
    """
    target_provider = provider or settings.DEFAULT_LLM_PROVIDER

    if target_provider == "gemini":
        target_model = model_name or settings.GEMINI_POWER_MODEL
        logger.info(f"Instantiating Gemini model: {target_model}")

        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not found. Ensure it is set in .env")

        try:
            return ChatGoogleGenerativeAI(
                model=target_model,
                temperature=0,
                google_api_key=settings.GOOGLE_API_KEY,
                convert_system_message_to_human=True,
            )
        except Exception as e:
            logger.error(f"Failed to instantiate Gemini {target_model}: {e}")
            # NOTE: A common error for gemini-1.5-flash-latest is a 404 if the model isn't available in the region.
            raise e

    elif target_provider == "huggingface":
        target_model = model_name or settings.HF_MODEL
        logger.info(f"Instantiating Hugging Face model: {target_model}")

        if not settings.HUGGINGFACEHUB_API_TOKEN:
            logger.warning(
                "HUGGINGFACEHUB_API_TOKEN not found. Ensure it is set in .env"
            )

        llm = HuggingFaceEndpoint(
            repo_id=target_model,
            task="text-generation",
            max_new_tokens=512,
            do_sample=False,
            huggingfacehub_api_token=settings.HUGGINGFACEHUB_API_TOKEN,
        )
        return ChatHuggingFace(llm=llm)

    else:
        raise ValueError(f"Unsupported provider: {target_provider}")
