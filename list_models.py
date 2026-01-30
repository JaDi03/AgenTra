
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load env vars from .env file
load_dotenv()
# Correct variable name found in main.py
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY not found in environment variables.")
else:
    genai.configure(api_key=api_key)
    print("Listing available models...")
    try:
        # Using the older access pattern which seems to be what the installed package supports
        # based on the import in agent_logic.py
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
