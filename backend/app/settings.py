from functools import cached_property
from os import getenv

from dotenv import load_dotenv


load_dotenv()


class Settings:
    @property
    def openai_api_key(self) -> str:
        return getenv("OPENAI_API_KEY", "")

    @property
    def openai_base_url(self) -> str:
        return getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    @property
    def ollama_base_url(self) -> str:
        return getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    @property
    def database_path(self) -> str:
        return getenv("DATABASE_PATH", "chat_memory.db")

    @property
    def app_title(self) -> str:
        return getenv("APP_TITLE", "Classic Chat Assistant")

    @cached_property
    def default_models(self) -> list[str]:
        raw = getenv("DEFAULT_MODELS", "gpt-4o-mini,ollama:llama3.1")
        return [item.strip() for item in raw.split(",") if item.strip()]


settings = Settings()
