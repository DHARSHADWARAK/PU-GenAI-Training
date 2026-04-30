from __future__ import annotations

from pathlib import Path

from .base import BaseDocumentLoader
from .file_loader import PdfDocumentLoader, TextDocumentLoader


class DocumentLoaderFactory:
    def __init__(self) -> None:
        self._loaders: list[BaseDocumentLoader] = [
            TextDocumentLoader(),
            PdfDocumentLoader(),
        ]

    def get_loader_for_path(self, file_path: str | Path) -> BaseDocumentLoader:
        suffix = Path(file_path).suffix.lower()
        for loader in self._loaders:
            if suffix in loader.supported_extensions:
                return loader
        raise ValueError(f"No loader registered for extension: {suffix}")

    def available_loaders(self) -> list[str]:
        return [loader.__class__.__name__ for loader in self._loaders]
