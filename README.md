# Kava Sakhi — AI Chatbot (Client-Server Architecture)

AI chatbot project, proper **server + frontend** architecture sathe.

## Folder Structure

```
kava-sakhi/
├── server/                        # Backend: API + data + AI logic
│   ├── app.py                     # Flask app entry point (routes)
│   ├── config.py                  # Env variable config
│   ├── controllers/
│   │   └── chat_controller.py     # Business logic (orchestrates service + data)
│   ├── services/
│   │   └── openai_service.py      # OpenAI API wrapper
│   ├── data/
│   │   ├── data_manager.py        # Chat history storage (JSON file)
│   │   └── chat_history.json      # Auto-created on first run
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                      # Frontend: GUI only (no business logic)
│   ├── main.py                    # CustomTkinter chat window
│   └── requirements.txt
│
└── README.md                      # This file
```

## Architecture Explanation

- **server/** — Real backend. Flask API expose kare chhe (`/api/chat`, `/api/history`, `/api/reset`). Andar 3 layers chhe:
  - `controllers/` → request ne handle kare, service + data ne coordinate kare
  - `services/` → OpenAI sathe direct vaat kare (isolated, so provider badalvo hoy to ahi j change karvanu)
  - `data/` → chat history save/load kare (JSON file, pachi thi database ma switch kari shakay)
- **frontend/** — Fakt GUI. Ahi koi OpenAI call nathi — badhu server ne HTTP request thi call kare chhe. Etle GUI ne backend thi completely alag rakhi shakay (kale web frontend banavo to backend same j rahese).

## How to Run

### Step 1 — Setup server
```bash
cd server
pip install -r requirements.txt
```
`.env.example` nu naam `.env` karo, ane tamari API key nakho:
```
OPENAI_API_KEY=sk-xxxxxxxxxxxx
```

Server start karo:
```bash
python app.py
```
Server `http://127.0.0.1:5000` par run thashe. Terminal khulli rakho.

### Step 2 — Setup frontend (naya terminal ma)
```bash
cd frontend
pip install -r requirements.txt
python main.py
```

GUI window khulse. Server pehla chalu hovu joie, nahi to GUI ma warning dekhashe.

## API Endpoints (server)

| Method | Endpoint                  | Description                    |
|--------|----------------------------|---------------------------------|
| GET    | `/health`                  | Server chalu chhe ke nai check |
| POST   | `/api/chat`                | Message mokli response levu    |
| GET    | `/api/history/<session_id>`| Chat history levi              |
| POST   | `/api/reset/<session_id>`  | Session reset karvi            |

`/api/chat` body:
```json
{ "session_id": "abc-123", "message": "Hello!" }
```

## Notes
- Chat history `server/data/chat_history.json` ma save thay chhe — session_id thi alag alag conversations rakhi shakay chhe.
- Model badalvo hoy to `server/.env` ma `OPENAI_MODEL` change karo.
- Future ma database (SQLite/PostgreSQL) add karvu hoy to fakt `data/data_manager.py` badalvani jarur — controller ke frontend ne kai touch nathi karvanu.
