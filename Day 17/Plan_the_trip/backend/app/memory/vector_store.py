import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)


class PreferenceVectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_dir = Path(settings.vector_store_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.records_path = self.base_dir / "records.json"
        self.index_path = self.base_dir / "faiss.index"
        self.records: list[dict[str, Any]] = self._load_records()
        self.index = None
        self._load_index()

    def _embed(self, text: str) -> np.ndarray:
        vector = np.zeros(128, dtype="float32")
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            vector[int.from_bytes(digest[:2], "big") % 128] += 1.0
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    def _load_records(self) -> list[dict[str, Any]]:
        if not self.records_path.exists():
            return []
        return json.loads(self.records_path.read_text(encoding="utf-8"))

    def _save_records(self) -> None:
        self.records_path.write_text(json.dumps(self.records, indent=2, default=str), encoding="utf-8")

    def _load_index(self) -> None:
        try:
            import faiss

            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
            else:
                self.index = faiss.IndexFlatIP(128)
                if self.records:
                    vectors = np.vstack([self._embed(record["text"]) for record in self.records])
                    self.index.add(vectors)
        except Exception as exc:
            logger.warning("FAISS unavailable; memory retrieval will use numpy similarity: %s", exc)
            self.index = None

    def _save_index(self) -> None:
        if self.index is None:
            return
        try:
            import faiss

            faiss.write_index(self.index, str(self.index_path))
        except Exception as exc:
            logger.warning("Failed to persist FAISS index: %s", exc)

    def add_trip(self, user_id: str, trip: dict[str, Any]) -> None:
        text = json.dumps(trip, default=str)
        record = {"user_id": user_id, "text": text, "trip": trip}
        self.records.append(record)
        vector = self._embed(text).reshape(1, -1)
        if self.index is not None:
            self.index.add(vector)
            self._save_index()
        self._save_records()

    def search(self, user_id: str, query: str, k: int = 3) -> list[dict[str, Any]]:
        if not self.records:
            return []
        query_vector = self._embed(query)
        scored = []
        for record in self.records:
            if record.get("user_id") != user_id:
                continue
            score = float(np.dot(query_vector, self._embed(record["text"])))
            scored.append((score, record))
        return [record for _, record in sorted(scored, key=lambda item: item[0], reverse=True)[:k]]


vector_store = PreferenceVectorStore()
