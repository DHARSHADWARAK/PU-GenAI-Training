from __future__ import annotations

import re

from chunkers.base import BaseChunker, Chunk
from embeddings.base import BaseEmbedder
from utils.text import cosine_similarity, normalize_text, split_sentences


class FixedChunker(BaseChunker):
    name = "fixed"

    def __init__(self, chunk_size: int = 800, overlap: int = 100) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[Chunk]:
        text = normalize_text(text)
        step = max(self.chunk_size - self.overlap, 1)
        chunks: list[Chunk] = []

        start = 0
        while start < len(text):
            chunk_text = text[start : start + self.chunk_size].strip()
            if chunk_text:
                chunks.append(Chunk(text=chunk_text, index=len(chunks)))
            start += step
        return chunks


class ParagraphChunker(BaseChunker):
    name = "paragraph"

    def __init__(self, chunk_size: int = 800) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[Chunk]:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalize_text(text)) if part.strip()]
        chunks: list[Chunk] = []
        current = ""

        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(Chunk(text=current, index=len(chunks)))
                current = paragraph

        if current:
            chunks.append(Chunk(text=current, index=len(chunks)))
        return chunks


class SentenceChunker(BaseChunker):
    name = "sentence"

    def __init__(self, chunk_size: int = 800, overlap: int = 100) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[Chunk]:
        sentences = split_sentences(text)
        chunks: list[Chunk] = []
        current: list[str] = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)
            if current and current_length + sentence_length + 1 > self.chunk_size:
                saved = " ".join(current).strip()
                if saved:
                    chunks.append(Chunk(text=saved, index=len(chunks)))
                overlap_text = saved[-self.overlap :].strip() if self.overlap > 0 else ""
                current = [overlap_text, sentence] if overlap_text else [sentence]
                current_length = len(" ".join(current))
            else:
                current.append(sentence)
                current_length += sentence_length + (1 if current_length else 0)

        if current:
            chunks.append(Chunk(text=" ".join(current).strip(), index=len(chunks)))
        return [chunk for chunk in chunks if chunk.text]


class RecursiveChunker(BaseChunker):
    name = "recursive"

    def __init__(self, chunk_size: int = 800, overlap: int = 100, separators: list[str] | None = None) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, text: str) -> list[Chunk]:
        text = normalize_text(text)
        fixed_fallback = FixedChunker(chunk_size=self.chunk_size, overlap=self.overlap)

        def split_recursively(segment: str, separators: list[str]) -> list[str]:
            segment = segment.strip()
            if not segment:
                return []
            if len(segment) <= self.chunk_size:
                return [segment]
            if not separators:
                return [chunk.text for chunk in fixed_fallback.chunk(segment)]

            separator = separators[0]
            if separator == "":
                return [chunk.text for chunk in fixed_fallback.chunk(segment)]

            parts = segment.split(separator)
            if len(parts) == 1:
                return split_recursively(segment, separators[1:])

            merged: list[str] = []
            current = ""
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                candidate = f"{current}{separator}{part}".strip() if current else part
                if len(candidate) <= self.chunk_size:
                    current = candidate
                else:
                    if current:
                        merged.extend(split_recursively(current, separators[1:]))
                    current = part

            if current:
                merged.extend(split_recursively(current, separators[1:]))
            return merged

        chunk_texts = split_recursively(text, self.separators)
        return [Chunk(text=value, index=index) for index, value in enumerate(chunk_texts)]


class SemanticChunker(BaseChunker):
    name = "semantic"

    def __init__(
        self,
        embedder: BaseEmbedder,
        chunk_size: int = 800,
        similarity_threshold: float = 0.82,
    ) -> None:
        self.embedder = embedder
        self.chunk_size = chunk_size
        self.similarity_threshold = similarity_threshold

    def chunk(self, text: str) -> list[Chunk]:
        sentences = split_sentences(text)
        if not sentences:
            return []

        embeddings = [self.embedder.embed(sentence) for sentence in sentences]
        chunks: list[Chunk] = []
        current_sentences = [sentences[0]]
        current_length = len(sentences[0])

        for index in range(1, len(sentences)):
            sentence = sentences[index]
            similarity = cosine_similarity(embeddings[index - 1], embeddings[index])
            would_exceed = current_length + len(sentence) + 1 > self.chunk_size

            if would_exceed or similarity < self.similarity_threshold:
                chunks.append(Chunk(text=" ".join(current_sentences).strip(), index=len(chunks)))
                current_sentences = [sentence]
                current_length = len(sentence)
            else:
                current_sentences.append(sentence)
                current_length += len(sentence) + 1

        if current_sentences:
            chunks.append(Chunk(text=" ".join(current_sentences).strip(), index=len(chunks)))
        return [chunk for chunk in chunks if chunk.text]
