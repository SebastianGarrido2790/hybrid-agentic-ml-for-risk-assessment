"""
Script to verify the Gemini API integration via LangChain.

This script uses the `langchain-google-genai` integration to test the
chat completion capabilities. It confirms that the `AgentSettings` and
LangChain wrapper are correctly configured to communicate with Gemini.

Usage:
    uv run python scripts/verify_gemini.py
"""

from src.agents.config import get_agent_settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

settings = get_agent_settings()
print(f"Testing model: {settings.GEMINI_POWER_MODEL}")

try:
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_POWER_MODEL,
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    res = llm.invoke([HumanMessage(content="Hello, are you working?")])
    print("Success! Response:")
    print(res.content)
except Exception as e:
    print(f"Error: {e}")
