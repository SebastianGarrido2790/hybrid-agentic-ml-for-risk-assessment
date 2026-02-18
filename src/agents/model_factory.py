"""
LLM Factory for the Agentic Reasoning Engine.

This module provides a factory function `get_llm` to instantiate and configure
Large Language Models (LLMs) from different providers (Google Gemini or Hugging Face)
abstracting the initialization complexity from the rest of the application.
"""

from typing import Literal
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from src.agents.config import get_agent_settings
import logging

# Configure logger
logger = logging.getLogger(__name__)

settings = get_agent_settings()


def get_llm(provider: Literal["gemini", "huggingface"] = "gemini") -> BaseChatModel:
    """
    Factory to return the configured LLM based on provider.

    Args:
        provider: 'gemini' (Cloud) or 'huggingface' (Local/Inference API)

    Returns:
        BaseChatModel: A LangChain compatible chat model.
    """
    if provider == "gemini":
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not found. Ensure it is set in .env")

        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            temperature=0,
            google_api_key=settings.GOOGLE_API_KEY,
            convert_system_message_to_human=True,  # Gemini specific tweak
        )

    elif provider == "huggingface":
        if not settings.HUGGINGFACEHUB_API_TOKEN:
            logger.warning(
                "HUGGINGFACEHUB_API_TOKEN not found. Ensure it is set in .env"
            )

        # Use Inference Endpoint
        llm = HuggingFaceEndpoint(
            repo_id=settings.HF_MODEL,
            task="text-generation",
            max_new_tokens=512,
            do_sample=False,
            huggingfacehub_api_token=settings.HUGGINGFACEHUB_API_TOKEN,
        )
        return ChatHuggingFace(llm=llm)

    else:
        raise ValueError(f"Unsupported provider: {provider}")
