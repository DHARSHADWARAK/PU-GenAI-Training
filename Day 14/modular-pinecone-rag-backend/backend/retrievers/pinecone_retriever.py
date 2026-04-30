from __future__ import annotations

from embeddings.base import BaseEmbedder
from vectorstores.base import BaseVectorStore

from .base import BaseRetriever


class PineconeRetriever(BaseRetriever):
    name = "pinecone"

    def __init__(self, embedder: BaseEmbedder, vector_store: BaseVectorStore) -> None:
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int, namespace: str) -> list[dict]:
        query_vector = self.embedder.embed(query)
        return self.vector_store.query(query_vector, top_k=top_k, namespace=namespace)
