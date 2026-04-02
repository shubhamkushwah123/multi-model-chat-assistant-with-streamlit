from __future__ import annotations

from typing import Iterable

import httpx
from openai import OpenAI

from .settings import settings


class LLMService:
    def __init__(self) -> None:
        self._openai_client = None
        if settings.openai_api_key:
            self._openai_client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )

    def available_models(self) -> list[dict[str, str]]:
        models = []
        for raw_model in settings.default_models:
            provider = "ollama" if raw_model.startswith("ollama:") else "openai"
            models.append(
                {
                    "id": raw_model,
                    "label": raw_model.replace("ollama:", ""),
                    "provider": provider,
                }
            )
        return models

    def generate_many(
        self, model_ids: Iterable[str], conversation: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        responses = []
        for model_id in model_ids:
            content = self.generate_one(model_id=model_id, conversation=conversation)
            responses.append({"model": model_id, "content": content})
        return responses

    def generate_one(self, model_id: str, conversation: list[dict[str, str]]) -> str:
        if model_id.startswith("ollama:"):
            return self._generate_with_ollama(model_id.split(":", 1)[1], conversation)
        return self._generate_with_openai(model_id, conversation)

    def _generate_with_openai(
        self, model_id: str, conversation: list[dict[str, str]]
    ) -> str:
        if self._openai_client is None:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Add it to your environment or .env file."
            )

        response = self._openai_client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": item["role"], "content": item["content"]} for item in conversation
            ],
        )
        return response.choices[0].message.content or ""

    def _generate_with_ollama(
        self, model_name: str, conversation: list[dict[str, str]]
    ) -> str:
        payload = {
            "model": model_name,
            "messages": [
                {"role": item["role"], "content": item["content"]} for item in conversation
            ],
            "stream": False,
        }
        with httpx.Client(timeout=120) as client:
            response = client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return data["message"]["content"]
