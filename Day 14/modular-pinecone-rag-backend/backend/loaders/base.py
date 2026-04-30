from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Document:
    source: str
    text: str


class BaseDocumentLoader(ABC):
    supported_extensions: tuple[str, ...] = ()

    @abstractmethod
    def load(self, file_path: str | Path) -> Document:
        raise NotImplementedError
