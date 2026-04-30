from __future__ import annotations

from pathlib import Path

from chunkers.base import Chunk
from schemas import IngestOptions
from services.container import AppContainer


class IngestionService:
    def __init__(self, container: AppContainer) -> None:
        self.container = container

    def ingest_file(self, file_path: str | Path, options: IngestOptions) -> dict:
        loader = self.container.loader_factory.get_loader_for_path(file_path)
        document = loader.load(file_path)
        chunker = self.container.chunker_factory.create(
            options.chunker,
            chunk_size=options.chunk_size,
            overlap=options.chunk_overlap,
            similarity_threshold=options.similarity_threshold,
        )
        chunks = chunker.chunk(document.text)
        vectors = self._build_vectors(chunks, source=document.source, namespace=options.namespace, chunker=options.chunker)
        self.container.vector_store.upsert(vectors=vectors, namespace=options.namespace)

        return {
            "file_name": Path(file_path).name,
            "file_path": str(file_path),
            "namespace": options.namespace,
            "chunker": options.chunker,
            "chunks_indexed": len(chunks),
            "index_name": self.container.vector_store.index_name,
        }

    def _build_vectors(self, chunks: list[Chunk], *, source: str, namespace: str, chunker: str) -> list[dict]:
        vectors: list[dict] = []
        source_name = Path(source).name
        for chunk in chunks:
            embedding = self.container.embedder.embed(chunk.text)
            vectors.append(
                {
                    "id": f"{namespace}:{source_name}:{chunker}:{chunk.index}",
                    "values": embedding,
                    "metadata": {
                        "text": chunk.text,
                        "source": source,
                        "chunk_index": chunk.index,
                        "chunker": chunker,
                    },
                }
            )
        return vectors
