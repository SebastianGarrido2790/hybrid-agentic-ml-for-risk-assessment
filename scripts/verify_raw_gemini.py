"""
Script to verify the raw Google Gemini API integration.

This script uses the `google-generativeai` library directly to list available models
and attempt a content generation request. It serves as a diagnostic tool to ensure
that the API key is valid and the model is accessible without LangChain's abstraction.

Usage:
    uv run python scripts/verify_raw_gemini.py
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Try gemini key
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("NO API KEY FOUND")
    exit(1)

genai.configure(api_key=api_key)

print("Listing available models:")
try:
    with open("available_models.txt", "w") as f:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                print(m.name)
                f.write(m.name + "\n")

    print("\nAttempting generation with gemini-pro-latest...")
    model = genai.GenerativeModel("gemini-pro-latest")
    response = model.generate_content("Hello")
    print("Success! Response:")
    print(response.text)
except Exception as e:
    print(f"\nError: {e}")
