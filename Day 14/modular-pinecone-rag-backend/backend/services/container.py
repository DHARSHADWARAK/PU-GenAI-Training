from __future__ import annotations

from chunkers.factory import ChunkerFactory
from embeddings import OpenAIEmbedder
from loaders import DocumentLoaderFactory
from retrievers.factory import RetrieverFactory
from vectorstores import PineconeVectorStore


class AppContainer:
    def __init__(self) -> None:
        self.loader_factory = DocumentLoaderFactory()
        self._embedder: OpenAIEmbedder | None = None
        self._chunker_factory: ChunkerFactory | None = None
        self._vector_store: PineconeVectorStore | None = None
        self._retriever_factory: RetrieverFactory | None = None

    @property
    def embedder(self) -> OpenAIEmbedder:
        if self._embedder is None:
            self._embedder = OpenAIEmbedder()
        return self._embedder

    @property
    def chunker_factory(self) -> ChunkerFactory:
        if self._chunker_factory is None:
            self._chunker_factory = ChunkerFactory(embedder=self.embedder)
        return self._chunker_factory

    @property
    def vector_store(self) -> PineconeVectorStore:
        if self._vector_store is None:
            self._vector_store = PineconeVectorStore()
        return self._vector_store

    @property
    def retriever_factory(self) -> RetrieverFactory:
        if self._retriever_factory is None:
            self._retriever_factory = RetrieverFactory(
                embedder=self.embedder,
                vector_store=self.vector_store,
            )
        return self._retriever_factory
