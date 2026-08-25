"""
app.py
Entry point for the server. Defines the API routes and delegates
all logic to the controller layer. Run this file to start the
local API server that the frontend GUI talks to.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from controllers.chat_controller import ChatController
from config import Config

app = Flask(__name__)
CORS(app)  # allow the frontend to call this server


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Body: { "session_id": "default", "message": "hello" }
    Returns: { "reply": "..." }
    """
    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id", "default")
    message = body.get("message", "")

    result, status_code = ChatController.handle_message(session_id, message)
    return jsonify(result), status_code


@app.route("/api/history/<session_id>", methods=["GET"])
def history(session_id):
    result, status_code = ChatController.get_history(session_id)
    return jsonify(result), status_code


@app.route("/api/reset/<session_id>", methods=["POST"])
def reset(session_id):
    result, status_code = ChatController.reset_session(session_id)
    return jsonify(result), status_code


if __name__ == "__main__":
    print(f"Starting server on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
