from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.observability.langsmith import configure_langsmith

load_dotenv()
BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "AI Trip Planner"
    app_env: str = "development"
    app_base_url: str = "http://localhost:8000"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openweather_api_key: str | None = None
    aviationstack_api_key: str | None = None
    geoapify_api_key: str | None = None
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "ai-trip-planner"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    vector_store_dir: Path = Path("storage/vector_store")
    pdf_output_dir: Path = Path("storage/pdfs")
    request_timeout_seconds: float = 18.0
    max_agent_retries: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if os.getenv("LANGSMITH_TRACING", "").lower() in {"true", "1", "yes"}:
        settings.langsmith_tracing = True
    if not settings.vector_store_dir.is_absolute():
        settings.vector_store_dir = BACKEND_ROOT / settings.vector_store_dir
    if not settings.pdf_output_dir.is_absolute():
        settings.pdf_output_dir = BACKEND_ROOT / settings.pdf_output_dir
    settings.vector_store_dir.mkdir(parents=True, exist_ok=True)
    settings.pdf_output_dir.mkdir(parents=True, exist_ok=True)
    configure_langsmith(settings)
    return settings
