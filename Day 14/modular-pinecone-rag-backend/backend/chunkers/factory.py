from __future__ import annotations

from embeddings.base import BaseEmbedder

from .base import BaseChunker
from .strategies import (
    FixedChunker,
    ParagraphChunker,
    RecursiveChunker,
    SemanticChunker,
    SentenceChunker,
)


class ChunkerFactory:
    def __init__(self, embedder: BaseEmbedder) -> None:
        self.embedder = embedder

    def create(
        self,
        name: str,
        *,
        chunk_size: int,
        overlap: int,
        similarity_threshold: float,
    ) -> BaseChunker:
        normalized = name.lower()
        if normalized == "fixed":
            return FixedChunker(chunk_size=chunk_size, overlap=overlap)
        if normalized == "paragraph":
            return ParagraphChunker(chunk_size=chunk_size)
        if normalized == "sentence":
            return SentenceChunker(chunk_size=chunk_size, overlap=overlap)
        if normalized == "recursive":
            return RecursiveChunker(chunk_size=chunk_size, overlap=overlap)
        if normalized == "semantic":
            return SemanticChunker(
                embedder=self.embedder,
                chunk_size=chunk_size,
                similarity_threshold=similarity_threshold,
            )
        raise ValueError(f"Unsupported chunker: {name}")

    @staticmethod
    def available_chunkers() -> list[str]:
        return ["fixed", "paragraph", "sentence", "recursive", "semantic"]
