from __future__ import annotations

from openai import OpenAI

from config import settings
from .base import BaseEmbedder


class OpenAIEmbedder(BaseEmbedder):
    def __init__(self, client: OpenAI | None = None, model: str | None = None) -> None:
        if client is None and not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for embedding operations.")
        self.client = client or OpenAI(api_key=settings.openai_api_key)
        self.model = model or settings.openai_embedding_model

    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding
