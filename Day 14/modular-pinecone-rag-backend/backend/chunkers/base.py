from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    index: int


class BaseChunker(ABC):
    name: str = "base"

    @abstractmethod
    def chunk(self, text: str) -> list[Chunk]:
        raise NotImplementedError
