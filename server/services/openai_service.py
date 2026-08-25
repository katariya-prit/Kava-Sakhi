"""
services/openai_service.py
Handles all direct communication with the AI provider (Groq, using
the OpenAI-compatible client). Keeping this isolated means if you
ever swap providers again, you only change this file.
"""

from openai import OpenAI
from config import Config


class OpenAIService:
    def __init__(self):
        self.client = None
        if Config.OPENAI_API_KEY:
            self.client = OpenAI(
                api_key=Config.OPENAI_API_KEY,
                base_url=Config.OPENAI_BASE_URL,
            )
        print(f"[DEBUG] Using base_url: {Config.OPENAI_BASE_URL}")
        print(f"[DEBUG] Using model: {Config.OPENAI_MODEL}")

    def is_configured(self):
        return self.client is not None

    def get_chat_response(self, messages: list) -> str:
        if not self.client:
            raise RuntimeError("API key not configured on server.")

        response = self.client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content.strip()