"""
config.py
Central configuration for the server. Loads environment variables
(like the API key) so the rest of the app doesn't touch
os.getenv directly.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "llama3.2:3b")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    HOST = os.getenv("SERVER_HOST", "127.0.0.1")
    PORT = int(os.getenv("SERVER_PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True") == "True"