"""
Script to verify Hugging Face Inference API integration.

This script tests the connectivity to the Hugging Face Inference API using
the configured model (e.g., Zephyr-7B). It ensures that the API token is valid
and that text generation can be performed using the remote inference endpoints.

Usage:
    uv run python scripts/verify_hf.py
"""

from langchain_huggingface import HuggingFaceEndpoint
from src.agents.config import get_agent_settings

settings = get_agent_settings()
print(f"Token present: {bool(settings.HUGGINGFACEHUB_API_TOKEN)}")
print(f"Model: {settings.HF_MODEL}")

try:
    print(f"Testing with {settings.HF_MODEL}...")
    llm = HuggingFaceEndpoint(
        repo_id=settings.HF_MODEL,
        task="text-generation",
        huggingfacehub_api_token=settings.HUGGINGFACEHUB_API_TOKEN,
    )
    print("Initialization successful.")
    res = llm.invoke("Hello!")
    print("Response:", res)
except Exception as e:
    print(f"Error: {e}")
