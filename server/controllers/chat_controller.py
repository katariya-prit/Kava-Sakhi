"""
controllers/chat_controller.py
Business logic layer. The Flask routes in app.py stay thin and just
call into this controller, which coordinates the data layer
(DataManager) and the AI service (OpenAIService).
"""

from services.openai_service import OpenAIService
from data.data_manager import DataManager

openai_service = OpenAIService()
data_manager = DataManager()


class ChatController:

    @staticmethod
    def handle_message(session_id: str, user_message: str) -> dict:
        """
        Full flow for one chat turn:
        1. Save user message
        2. Build message history for this session
        3. Call OpenAI
        4. Save assistant reply
        5. Return reply to caller
        """
        if not user_message or not user_message.strip():
            return {"error": "Empty message."}, 400

        if not openai_service.is_configured():
            return {"error": "Server has no OPENAI_API_KEY configured."}, 500

        # Save user's message
        data_manager.append_message(session_id, "user", user_message)

        # Get full history for context
        history = data_manager.get_session(session_id)

        try:
            reply = openai_service.get_chat_response(history)
        except Exception as e:
            print(f"[ERROR] OpenAI call failed: {e}")  # debug: terminal ma full error dekhase
            return {"error": str(e)}, 500

        # Save assistant's reply
        data_manager.append_message(session_id, "assistant", reply)

        return {"reply": reply}, 200

    @staticmethod
    def get_history(session_id: str) -> dict:
        messages = data_manager.get_session(session_id)
        # Hide the system prompt from the client
        visible = [m for m in messages if m["role"] != "system"]
        return {"messages": visible}, 200

    @staticmethod
    def reset_session(session_id: str) -> dict:
        data_manager.clear_session(session_id)
        return {"status": "cleared"}, 200