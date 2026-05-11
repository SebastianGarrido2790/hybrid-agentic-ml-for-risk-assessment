"""
Unit tests for model_factory.py.
"""

from unittest.mock import patch

import pytest

from src.agents.model_factory import get_llm


@patch("src.agents.model_factory.ChatGoogleGenerativeAI")
@patch("src.agents.model_factory.settings")
def test_get_llm_gemini(mock_settings, mock_gemini):
    """Test getting Gemini model."""
    mock_settings.DEFAULT_LLM_PROVIDER = "gemini"
    mock_settings.GEMINI_POWER_MODEL = "gemini-test"
    mock_settings.GOOGLE_API_KEY = "test-key"

    get_llm(provider="gemini")

    mock_gemini.assert_called_once()
    args, kwargs = mock_gemini.call_args
    assert kwargs["model"] == "gemini-test"
    assert kwargs["google_api_key"] == "test-key"


@patch("src.agents.model_factory.ChatHuggingFace")
@patch("src.agents.model_factory.HuggingFaceEndpoint")
@patch("src.agents.model_factory.settings")
def test_get_llm_huggingface(mock_settings, mock_hf_endpoint, mock_chat_hf):
    """Test getting HuggingFace model."""
    mock_settings.DEFAULT_LLM_PROVIDER = "huggingface"
    mock_settings.HF_MODEL = "hf-test"
    mock_settings.HUGGINGFACEHUB_API_TOKEN = "test-token"

    get_llm(provider="huggingface")

    mock_hf_endpoint.assert_called_once()
    args, kwargs = mock_hf_endpoint.call_args
    assert kwargs["repo_id"] == "hf-test"
    assert kwargs["huggingfacehub_api_token"] == "test-token"
    mock_chat_hf.assert_called_once()


def test_get_llm_invalid_provider():
    """Test invalid provider raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported provider"):
        get_llm(provider="invalid")
