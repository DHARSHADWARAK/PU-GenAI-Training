from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
UPLOADS_DIR = BACKEND_DIR / "uploads"


def _load_env() -> None:
    for env_path in (PROJECT_ROOT / ".env", BACKEND_DIR / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


_load_env()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Modular Pinecone RAG Backend")
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    allow_origins_raw: str = os.getenv(
        "ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
    )

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    openai_chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "modular-rag-demo")
    pinecone_cloud: str = os.getenv("PINECONE_CLOUD", "aws")
    pinecone_region: str = os.getenv("PINECONE_REGION", "us-east-1")
    pinecone_metric: str = os.getenv("PINECONE_METRIC", "cosine")
    pinecone_dimension: int = int(os.getenv("PINECONE_DIMENSION", "1536"))

    default_chunker: str = os.getenv("DEFAULT_CHUNKER", "recursive")
    default_chunk_size: int = int(os.getenv("DEFAULT_CHUNK_SIZE", "800"))
    default_chunk_overlap: int = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "100"))
    default_similarity_threshold: float = float(os.getenv("DEFAULT_SIMILARITY_THRESHOLD", "0.82"))
    default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "3"))
    default_retriever: str = os.getenv("DEFAULT_RETRIEVER", "pinecone")
    system_prompt: str = os.getenv(
        "RAG_SYSTEM_PROMPT",
        "Answer only from the provided context. If the context is insufficient, say so clearly.",
    )

    @property
    def allow_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allow_origins_raw.split(",") if origin.strip()]


settings = Settings()
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
