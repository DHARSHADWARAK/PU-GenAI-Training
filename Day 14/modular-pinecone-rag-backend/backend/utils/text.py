from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", cleaned) if sentence.strip()]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = sum(a * a for a in vec_a) ** 0.5
    magnitude_b = sum(b * b for b in vec_b) ** 0.5
    if not magnitude_a or not magnitude_b:
        return 0.0
    return dot_product / (magnitude_a * magnitude_b)
