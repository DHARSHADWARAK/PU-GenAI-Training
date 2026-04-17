from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"


def _load_env() -> None:
    for env_path in (PROJECT_ROOT / ".env", BACKEND_DIR / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


_load_env()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Customer Support AI")
    sarvam_api_key: str = os.getenv("SARVAM_API_KEY", "")
    sarvam_api_url: str = os.getenv(
        "SARVAM_API_URL",
        "https://api.sarvam.ai/v1/chat/completions",
    )
    sarvam_model: str = os.getenv("SARVAM_MODEL", "sarvam-105b")
    top_k: int = int(os.getenv("TOP_K", "3"))
    bm25_low_score_threshold: float = float(os.getenv("BM25_LOW_SCORE_THRESHOLD", "0.5"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "45"))
    allow_origins_raw: str = os.getenv(
        "ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )

    @property
    def policies_path(self) -> Path:
        return DATA_DIR / "policies.json"

    @property
    def log_file_path(self) -> Path:
        return LOGS_DIR / "app.log"

    @property
    def allow_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allow_origins_raw.split(",") if origin.strip()]


settings = Settings()
LOGS_DIR.mkdir(parents=True, exist_ok=True)
