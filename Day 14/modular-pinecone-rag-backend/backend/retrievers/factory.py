from __future__ import annotations

from embeddings.base import BaseEmbedder
from vectorstores.base import BaseVectorStore

from .base import BaseRetriever
from .pinecone_retriever import PineconeRetriever


class RetrieverFactory:
    def __init__(self, embedder: BaseEmbedder, vector_store: BaseVectorStore) -> None:
        self.embedder = embedder
        self.vector_store = vector_store

    def create(self, name: str) -> BaseRetriever:
        normalized = name.lower()
        if normalized == "pinecone":
            return PineconeRetriever(embedder=self.embedder, vector_store=self.vector_store)
        raise ValueError(f"Unsupported retriever: {name}")

    @staticmethod
    def available_retrievers() -> list[str]:
        return ["pinecone"]
