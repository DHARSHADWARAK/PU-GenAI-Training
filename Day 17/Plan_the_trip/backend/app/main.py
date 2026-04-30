import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.trip_service import plan_trip
from app.utils.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


class TripRequest(BaseModel):
    source: str | None = None
    destination: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    budget: float | None = Field(default=None, ge=0)
    currency: str = "INR"
    travellers: int = Field(default=1, ge=1)
    preferences: list[str] = Field(default_factory=list)
    pace: str = "balanced"
    user_id: str = "anonymous"
    name: str | None = None
    email: str | None = None


app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pdf_dir = Path(settings.pdf_output_dir)
pdf_dir.mkdir(parents=True, exist_ok=True)
app.mount("/pdfs", StaticFiles(directory=str(pdf_dir)), name="pdfs")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.post("/plan-trip")
async def plan_trip_endpoint(request: TripRequest) -> dict[str, Any]:
    try:
        payload = request.model_dump()
        result = await plan_trip(payload)
        if result.get("pdf_link"):
            result["pdf_link"] = f"{settings.app_base_url}{result['pdf_link']}"
        return result
    except Exception as exc:
        logger.exception("Trip planning failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
