from __future__ import annotations

from pinecone import Pinecone, ServerlessSpec

from config import settings
from .base import BaseVectorStore


class PineconeVectorStore(BaseVectorStore):
    def __init__(self) -> None:
        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is required for Pinecone vector store operations.")
        self.client = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self._ensure_index()
        self.index = self.client.Index(self.index_name)

    def _ensure_index(self) -> None:
        existing_indexes = self.client.list_indexes().names()
        if self.index_name in existing_indexes:
            return

        self.client.create_index(
            name=self.index_name,
            dimension=settings.pinecone_dimension,
            metric=settings.pinecone_metric,
            spec=ServerlessSpec(
                cloud=settings.pinecone_cloud,
                region=settings.pinecone_region,
            ),
        )

    def upsert(self, vectors: list[dict], namespace: str) -> None:
        self.index.upsert(vectors=vectors, namespace=namespace)

    def query(self, vector: list[float], top_k: int, namespace: str) -> list[dict]:
        result = self.index.query(
            vector=vector,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
        )
        return result.get("matches", [])
