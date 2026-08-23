from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class ChatModel(Protocol):
    model_name: str

    def chat(self, messages: list[dict[str, str]]) -> str: ...


@dataclass(frozen=True)
class OllamaCloudModel:
    model_name: str
    host: str = "https://ollama.com"

    def chat(self, messages: list[dict[str, str]]) -> str:
        api_key = os.environ.get("OLLAMA_API_KEY")
        if not api_key:
            raise RuntimeError("OLLAMA_API_KEY is required for live Ollama Cloud mode.")
        try:
            from ollama import Client
        except ImportError as exc:
            raise RuntimeError("Install the ollama package before using live mode.") from exc

        client = Client(
            host=self.host,
            headers={"Authorization": "Bearer " + api_key},
        )
        response = client.chat(model=self.model_name, messages=messages, stream=False)
        return response["message"]["content"]
