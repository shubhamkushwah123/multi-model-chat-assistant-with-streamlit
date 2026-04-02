# Classic Chat Assistant

A simple classic chat assistant built with FastAPI and Streamlit.

## Features

- Chat UI built in Streamlit
- FastAPI backend API
- Session memory stored in local SQLite
- Multi-model responses in one chat turn
- OpenAI-compatible models and Ollama models supported

## Project Structure

```text
backend/
  app/
    db.py
    llm.py
    main.py
    schemas.py
    settings.py
frontend/
  streamlit_app.py
.vscode/
  launch.json
requirements.txt
```

## Setup

1. Open the folder in VS Code.
2. Create a virtual environment:

```bash
python3 -m venv .venv
```

3. Activate it:

```bash
source .venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Copy the environment template:

```bash
cp .env.example .env
```

6. Edit `.env` with at least one working model source:

- For OpenAI:
  - set `OPENAI_API_KEY`
  - keep `DEFAULT_MODELS=gpt-4o-mini` or add more OpenAI model ids
- For Ollama:
  - make sure Ollama is running locally
  - use values like `DEFAULT_MODELS=ollama:llama3.1,ollama:mistral, ollama:gemma2b.b`

You can also mix providers, for example:

```env
DEFAULT_MODELS=gpt-4o-mini,ollama:llama3.1,ollama:gemma2b:b
```

## Run In VS Code

### Option 1: Run both services from the debugger

1. Open the Run and Debug panel in VS Code.
2. Choose `Run Full App`.
3. Start debugging.
4. Open:
   - Streamlit UI: `http://localhost:8501`
   - FastAPI docs: `http://localhost:8000/docs`

### Option 2: Run from the VS Code terminal

Start the backend:

```bash
source .venv/bin/activate
uvicorn backend.app.main:app --reload
```

In a second terminal, start the UI:

```bash
source .venv/bin/activate
streamlit run frontend/streamlit_app.py
```

## How It Works

- Each new chat gets a session id.
- Messages are saved to SQLite in `chat_memory.db`.
- When you send a prompt, the backend loads that session history as memory.
- The same prompt is sent to every selected model.
- Each model response is stored and shown separately in the UI.

## Notes

- If no OpenAI key is configured and you select an OpenAI model, the backend returns an error.
- If Ollama is not running and you select an Ollama model, the backend returns an error.
- SQLite storage is local to this project folder by default.


## Here is the screwnshot of the working app.
<img width="2926" height="1674" alt="image" src="https://github.com/user-attachments/assets/a03e54e7-9477-4556-862a-6f7cf8b69d09" />
