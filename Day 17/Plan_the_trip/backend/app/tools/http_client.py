import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


async def get_json(url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {"items": data}
    except Exception as exc:
        logger.warning("GET %s failed: %s", url, exc)
        return {"error": str(exc), "source": "fallback"}
