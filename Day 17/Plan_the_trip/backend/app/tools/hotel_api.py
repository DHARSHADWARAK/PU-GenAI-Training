from typing import Any

from app.config import get_settings
from app.tools.http_client import get_json


def _fallback_hotels(destination: str, nightly_budget: float) -> list[dict[str, Any]]:
    return [
        {
            "name": f"{destination} Comfort Stay",
            "price_per_night": round(nightly_budget * 0.8),
            "rating": 4.1,
            "category": "accommodation.hotel",
        },
        {
            "name": f"{destination} Central Hotel",
            "price_per_night": round(nightly_budget),
            "rating": 4.3,
            "category": "accommodation.hotel",
        },
        {
            "name": f"{destination} Premium Retreat",
            "price_per_night": round(nightly_budget * 1.35),
            "rating": 4.6,
            "category": "accommodation.hotel",
        },
    ]


def _geoapify_filter_from_feature(feature: dict[str, Any]) -> str:
    bbox = feature.get("bbox") or feature.get("properties", {}).get("bbox")
    props = feature.get("properties", {})
    if isinstance(bbox, list) and len(bbox) >= 4:
        west, south, east, north = bbox[:4]
        return f"rect:{west},{north},{east},{south}"
    lon = props.get("lon")
    lat = props.get("lat")
    return f"circle:{lon},{lat},12000"


def _estimate_nightly_price(nightly_budget: float, index: int) -> int:
    multipliers = [0.78, 0.9, 1.0, 1.12, 1.25, 1.4]
    multiplier = multipliers[index % len(multipliers)]
    return round(max(nightly_budget * multiplier, 1200))


async def fetch_hotels(destination: str, budget: float, travellers: int) -> dict[str, Any]:
    settings = get_settings()
    nightly_budget = max(float(budget) * 0.32 / max(travellers, 1) / 3, 1500)
    if not settings.geoapify_api_key:
        hotels = _fallback_hotels(destination, nightly_budget)
        return {"source": "fallback", "selected": hotels[1], "options": hotels}

    geocode = await get_json(
        "https://api.geoapify.com/v1/geocode/search",
        {"text": destination, "apiKey": settings.geoapify_api_key, "limit": 1},
    )
    features = geocode.get("features") or []
    if not features:
        hotels = _fallback_hotels(destination, nightly_budget)
        return {
            "source": "geoapify",
            "error": "Unable to geocode destination for hotel search.",
            "selected": hotels[1],
            "options": hotels,
        }

    search_filter = _geoapify_filter_from_feature(features[0])
    data = await get_json(
        "https://api.geoapify.com/v2/places",
        {
            "categories": "accommodation.hotel",
            "filter": search_filter,
            "limit": 20,
            "apiKey": settings.geoapify_api_key,
        },
    )
    if "error" in data:
        hotels = _fallback_hotels(destination, nightly_budget)
        return {**data, "selected": hotels[1], "options": hotels}

    options = []
    for index, feature in enumerate(data.get("features", [])[:8]):
        props = feature.get("properties", {})
        categories = props.get("categories") or []
        category_text = ",".join(categories)
        options.append(
            {
                "name": props.get("name") or props.get("formatted") or f"Commercial stay near {destination}",
                "price_per_night": _estimate_nightly_price(nightly_budget, index),
                "rating": round(4.0 + min(index, 5) * 0.08, 1),
                "address": props.get("formatted"),
                "category": category_text or "accommodation.hotel",
                "place_id": props.get("place_id"),
                "lat": props.get("lat"),
                "lon": props.get("lon"),
            }
        )
    if not options:
        options = _fallback_hotels(destination, nightly_budget)
    selected = sorted(options, key=lambda h: abs(h["price_per_night"] - nightly_budget))[0]
    return {"source": "geoapify", "selected": selected, "options": options, "filter": search_filter, "raw": data}
