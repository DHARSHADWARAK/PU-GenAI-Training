from __future__ import annotations

import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from config import settings


STOP_WORDS = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "for",
    "of", "and", "or", "with", "we", "our", "your", "can", "will",
    "be", "by", "as", "if", "up", "do", "not", "no", "so", "has",
    "was", "are", "this", "that", "have", "from", "i", "my", "me",
    "please", "hello", "hi", "want", "need", "get", "got",
}


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    cleaned = re.sub(r"[^\w\s]", " ", lowered)
    return [token for token in cleaned.split() if token not in STOP_WORDS and len(token) > 2]


def build_corpus(policies: list[dict]) -> list[list[str]]:
    corpus: list[list[str]] = []
    for policy in policies:
        tokens = (
            tokenize(policy.get("title", "")) * 3
            + tokenize(policy.get("category", "")) * 2
            + [keyword.lower() for keyword in policy.get("keywords", [])]
            + tokenize(policy.get("solution", ""))
            + tokenize(policy.get("alternate_solution", ""))
            + tokenize(policy.get("content", ""))
        )
        corpus.append(tokens)
    return corpus


class PolicyRetriever:
    def __init__(self, policies_path: str | Path | None = None):
        self.policies_path = Path(policies_path or settings.policies_path)
        self.policies = self._load_policies(self.policies_path)
        self.corpus = build_corpus(self.policies)
        self.bm25 = BM25Okapi(self.corpus)

    def _load_policies(self, path: Path) -> list[dict]:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def retrieve(self, query: str, top_k: int | None = None) -> dict:
        query_tokens = tokenize(query)
        chosen_top_k = top_k or settings.top_k

        if not query_tokens:
            return {
                "docs": [],
                "top_score": 0.0,
                "is_fallback": True,
                "query_tokens": [],
            }

        scores = self.bm25.get_scores(query_tokens)
        ranked = sorted(zip(self.policies, scores), key=lambda item: item[1], reverse=True)

        docs = []
        for policy, score in ranked[:chosen_top_k]:
            if score <= 0:
                continue
            docs.append({**policy, "bm25_score": round(float(score), 4)})

        top_score = docs[0]["bm25_score"] if docs else 0.0
        return {
            "docs": docs,
            "top_score": top_score,
            "is_fallback": top_score < settings.bm25_low_score_threshold,
            "query_tokens": query_tokens,
        }
