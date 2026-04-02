from __future__ import annotations

from datetime import datetime

import httpx
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(page_title="Classic Chat Assistant", page_icon="💬", layout="wide")
st.title("Classic Chat Assistant")
st.caption("Chat with one or more LLMs and keep your session memory saved locally.")


@st.cache_data(show_spinner=False)
def fetch_models() -> list[dict]:
    response = httpx.get(f"{API_BASE_URL}/models", timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_sessions() -> list[dict]:
    response = httpx.get(f"{API_BASE_URL}/sessions", timeout=10)
    response.raise_for_status()
    return response.json()


def create_session() -> dict:
    response = httpx.post(f"{API_BASE_URL}/sessions", timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_messages(session_id: str) -> list[dict]:
    response = httpx.get(f"{API_BASE_URL}/sessions/{session_id}/messages", timeout=10)
    response.raise_for_status()
    return response.json()


def send_message(session_id: str | None, message: str, models: list[str]) -> dict:
    response = httpx.post(
        f"{API_BASE_URL}/chat",
        json={"session_id": session_id, "message": message, "models": models},
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def format_timestamp(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%b %d, %I:%M %p")
    except ValueError:
        return value


if "session_id" not in st.session_state:
    st.session_state.session_id = None


with st.sidebar:
    st.subheader("Sessions")
    if st.button("New chat", use_container_width=True):
        session = create_session()
        st.session_state.session_id = session["id"]

    sessions = fetch_sessions()
    for session in sessions:
        if st.button(
            session["title"],
            key=session["id"],
            use_container_width=True,
            type="primary" if st.session_state.session_id == session["id"] else "secondary",
        ):
            st.session_state.session_id = session["id"]

    st.divider()
    st.subheader("Models")
    available_models = fetch_models()
    default_model_ids = [model["id"] for model in available_models[:1]]
    selected_models = st.multiselect(
        "Choose one or more models",
        options=[model["id"] for model in available_models],
        default=default_model_ids,
        help="The same prompt will be sent to each selected model.",
    )


if not st.session_state.session_id:
    session = create_session()
    st.session_state.session_id = session["id"]


messages = fetch_messages(st.session_state.session_id)

for message in messages:
    speaker = "assistant" if message["role"] == "assistant" else "user"
    with st.chat_message(speaker):
        if message["model"]:
            st.markdown(f"**{message['model']}**")
        st.write(message["content"])
        st.caption(format_timestamp(message["created_at"]))


prompt = st.chat_input("Send a message")
if prompt:
    if not selected_models:
        st.warning("Select at least one model before sending a message.")
        st.stop()

    with st.chat_message("user"):
        st.write(prompt)

    with st.spinner("Generating responses..."):
        data = send_message(st.session_state.session_id, prompt, selected_models)
        st.session_state.session_id = data["session_id"]
    st.rerun()
