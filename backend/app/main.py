from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .db import get_connection, init_db
from .llm import LLMService
from .schemas import ChatRequest, ChatResponse, MessageRecord, ModelInfo, SessionInfo
from .settings import settings


app = FastAPI(title=settings.app_title)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_service = LLMService()


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/models", response_model=list[ModelInfo])
def list_models() -> list[ModelInfo]:
    return [ModelInfo(**item) for item in llm_service.available_models()]


@app.get("/sessions", response_model=list[SessionInfo])
def list_sessions() -> list[SessionInfo]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, created_at
            FROM sessions
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [SessionInfo(**dict(row)) for row in rows]


@app.post("/sessions", response_model=SessionInfo)
def create_session() -> SessionInfo:
    session = {
        "id": str(uuid4()),
        "title": "New chat",
        "created_at": _now_iso(),
    }
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (id, title, created_at) VALUES (?, ?, ?)",
            (session["id"], session["title"], session["created_at"]),
        )
    return SessionInfo(**session)


@app.get("/sessions/{session_id}/messages", response_model=list[MessageRecord])
def get_messages(session_id: str) -> list[MessageRecord]:
    _ensure_session_exists(session_id)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT session_id, role, model, content, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()
    return [MessageRecord(**dict(row)) for row in rows]


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or create_session().id
    _ensure_session_exists(session_id)

    user_message = {
        "session_id": session_id,
        "role": "user",
        "model": None,
        "content": request.message.strip(),
        "created_at": _now_iso(),
    }
    if not user_message["content"]:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO messages (session_id, role, model, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_message["session_id"],
                user_message["role"],
                user_message["model"],
                user_message["content"],
                user_message["created_at"],
            ),
        )

    try:
        generated = [
            {
                "model": model_id,
                "content": llm_service.generate_one(
                    model_id=model_id,
                    conversation=_conversation_for_model(session_id, model_id),
                ),
            }
            for model_id in request.models
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    assistant_messages = []
    with get_connection() as conn:
        for item in generated:
            record = {
                "session_id": session_id,
                "role": "assistant",
                "model": item["model"],
                "content": item["content"],
                "created_at": _now_iso(),
            }
            assistant_messages.append(record)
            conn.execute(
                """
                INSERT INTO messages (session_id, role, model, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record["session_id"],
                    record["role"],
                    record["model"],
                    record["content"],
                    record["created_at"],
                ),
            )

    _update_session_title_if_needed(session_id=session_id, message=request.message)
    return ChatResponse(
        session_id=session_id,
        responses=[MessageRecord(**item) for item in assistant_messages],
    )


def _ensure_session_exists(session_id: str) -> None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found.")


def _conversation_for_model(session_id: str, model_id: str) -> list[dict[str, str]]:
    system_prompt = {
        "role": "system",
        "content": (
            "You are a helpful classic chat assistant. Be clear, accurate, and concise."
        ),
    }
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, model, content
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()
    conversation = [system_prompt]
    for row in rows:
        if row["role"] == "user" or row["model"] == model_id:
            conversation.append({"role": row["role"], "content": row["content"]})
    return conversation


def _update_session_title_if_needed(session_id: str, message: str) -> None:
    title = message.strip()[:40] or "New chat"
    with get_connection() as conn:
        row = conn.execute(
            "SELECT title FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if row and row["title"] == "New chat":
            conn.execute(
                "UPDATE sessions SET title = ? WHERE id = ?",
                (title, session_id),
            )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
