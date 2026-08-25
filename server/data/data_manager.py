"""
data/data_manager.py
Simple data layer for storing chat sessions.
Uses a local JSON file so the project has zero external DB
dependency out of the box. Swap this out for SQLite/Postgres/etc.
later without touching the controller or service layers.
"""

import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "chat_history.json")


class DataManager:
    def __init__(self):
        if not os.path.exists(DATA_FILE):
            self._write({"sessions": {}})

    # ---------------- internal helpers ----------------
    def _read(self):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ---------------- public API ----------------
    def get_session(self, session_id: str) -> list:
        """Return the message list for a session, creating one if needed."""
        data = self._read()
        if session_id not in data["sessions"]:
            data["sessions"][session_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "messages": [
                    {"role": "system", "content": "You are a helpful, friendly assistant."}
                ],
            }
            self._write(data)
        return data["sessions"][session_id]["messages"]

    def append_message(self, session_id: str, role: str, content: str):
        data = self._read()
        if session_id not in data["sessions"]:
            self.get_session(session_id)
            data = self._read()
        data["sessions"][session_id]["messages"].append(
            {"role": role, "content": content}
        )
        self._write(data)

    def clear_session(self, session_id: str):
        data = self._read()
        if session_id in data["sessions"]:
            del data["sessions"][session_id]
            self._write(data)
