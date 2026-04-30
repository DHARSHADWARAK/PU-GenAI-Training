from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from .base import BaseDocumentLoader, Document


class TextDocumentLoader(BaseDocumentLoader):
    supported_extensions = (".txt", ".md")

    def load(self, file_path: str | Path) -> Document:
        path = Path(file_path)
        return Document(source=str(path), text=path.read_text(encoding="utf-8"))


class PdfDocumentLoader(BaseDocumentLoader):
    supported_extensions = (".pdf",)

    def load(self, file_path: str | Path) -> Document:
        path = Path(file_path)
        reader = PdfReader(str(path))
        pages: list[str] = []
        for page in reader.pages:
            content = page.extract_text()
            if content:
                pages.append(content)
        return Document(source=str(path), text="\n".join(pages))
