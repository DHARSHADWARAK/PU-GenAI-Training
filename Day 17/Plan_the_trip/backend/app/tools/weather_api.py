from typing import Any

from app.config import get_settings
from app.tools.http_client import get_json


async def fetch_weather(destination: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openweather_api_key:
        return {
            "source": "fallback",
            "summary": "API key missing. Expect seasonal conditions and verify forecast before travel.",
            "temperature_c": None,
            "risk": "unknown",
        }
    data = await get_json(
        "https://api.openweathermap.org/data/2.5/weather",
        {"q": destination, "appid": settings.openweather_api_key, "units": "metric"},
    )
    if "error" in data:
        return data
    weather = (data.get("weather") or [{}])[0]
    main = data.get("main") or {}
    risk = "bad" if any(k in (weather.get("main", "").lower()) for k in ["rain", "storm", "snow"]) else "good"
    return {
        "source": "openweathermap",
        "city": data.get("name", destination),
        "summary": weather.get("description", "Weather available"),
        "temperature_c": main.get("temp"),
        "humidity": main.get("humidity"),
        "risk": risk,
        "raw": data,
    }
