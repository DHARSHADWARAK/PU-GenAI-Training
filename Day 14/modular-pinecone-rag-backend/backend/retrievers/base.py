from __future__ import annotations

from abc import ABC, abstractmethod


class BaseRetriever(ABC):
    name: str = "base"

    @abstractmethod
    def retrieve(self, query: str, top_k: int, namespace: str) -> list[dict]:
        raise NotImplementedError
