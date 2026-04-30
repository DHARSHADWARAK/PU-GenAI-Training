from __future__ import annotations

from abc import ABC, abstractmethod


class BaseVectorStore(ABC):
    @abstractmethod
    def upsert(self, vectors: list[dict], namespace: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def query(self, vector: list[float], top_k: int, namespace: str) -> list[dict]:
        raise NotImplementedError
