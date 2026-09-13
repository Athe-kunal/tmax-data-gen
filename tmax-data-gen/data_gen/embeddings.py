"""Thin OpenAI-compatible embeddings client.

Configuration comes entirely from environment variables so the backing
endpoint and model can be swapped later (a self-hosted vLLM embeddings
server, Azure OpenAI, or any other OpenAI-compatible provider) without code
changes:

    EMBEDDING_API_KEY   - API key. Falls back to OPENAI_API_KEY.
    EMBEDDING_BASE_URL  - Endpoint base URL. Unset uses the OpenAI default.
    EMBEDDING_MODEL     - Model name. Defaults to "text-embedding-3-small".
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI

_DEFAULT_MODEL = "text-embedding-3-small"


@dataclass(frozen=True)
class EmbeddingClientConfig:
    """Connection settings for an OpenAI-compatible embeddings endpoint."""

    api_key: str | None = None
    base_url: str | None = None
    model: str = _DEFAULT_MODEL

    @staticmethod
    def from_env() -> "EmbeddingClientConfig":
        return EmbeddingClientConfig(
            api_key=os.environ.get("EMBEDDING_API_KEY") or os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("EMBEDDING_BASE_URL"),
            model=os.environ.get("EMBEDDING_MODEL", _DEFAULT_MODEL),
        )


class EmbeddingClient:
    """Wraps an OpenAI-compatible `/embeddings` endpoint."""

    def __init__(self, config: EmbeddingClientConfig | None = None) -> None:
        self._config = config or EmbeddingClientConfig.from_env()
        self._client = OpenAI(api_key=self._config.api_key, base_url=self._config.base_url)

    @property
    def model(self) -> str:
        return self._config.model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Returns one embedding vector per input text, in the same order."""
        response = self._client.embeddings.create(model=self._config.model, input=texts)
        return [item.embedding for item in response.data]
