from typing import Any

from app.config import get_settings
from app.tools.http_client import get_json

INCLUDED_TOURIST_CATEGORIES = {
    "tourism.sights",
    "tourism.attraction",
    "entertainment.museum",
}
EXCLUDED_PRIMARY_CATEGORIES = (
    "commercial",
    "catering.restaurant",
)
PARIS_COORDINATES = {"lon": 2.3522, "lat": 48.8566}


def is_relevant_tourist_place(categories: list[str]) -> bool:
    if not categories:
        return False
    primary_category = categories[0]
    if primary_category.startswith(EXCLUDED_PRIMARY_CATEGORIES):
        return False
    return any(category in INCLUDED_TOURIST_CATEGORIES for category in categories)


def clean_place_feature(feature: dict[str, Any]) -> dict[str, Any] | None:
    props = feature.get("properties") or {}
    categories = props.get("categories") or []
    if not is_relevant_tourist_place(categories):
        return None

    name = props.get("name")
    address = props.get("formatted")
    lat = props.get("lat")
    lon = props.get("lon")
    if not name or lat is None or lon is None:
        return None

    return {
        "name": name,
        "address": address or "",
        "lat": lat,
        "lon": lon,
    }


def clean_geoapify_places(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned_places: list[dict[str, Any]] = []
    for feature in features:
        place = clean_place_feature(feature)
        if place:
            cleaned_places.append(place)
    return cleaned_places


async def fetch_places(destination: str, preferences: list[str], weather_risk: str = "unknown") -> dict[str, Any]:
    settings = get_settings()
    fallback_places = [
        {"name": f"{destination} heritage sight", "address": "", "lat": None, "lon": None},
        {"name": f"{destination} city museum", "address": "", "lat": None, "lon": None},
        {"name": f"{destination} landmark", "address": "", "lat": None, "lon": None},
    ]
    if weather_risk == "bad":
        fallback_places = [place for place in fallback_places if "museum" in place["name"].lower()] + fallback_places
    if not settings.geoapify_api_key:
        return {"source": "fallback", "places": fallback_places[:6], "weather_adjusted": weather_risk == "bad"}

    if destination.strip().lower() == "paris":
        lon = PARIS_COORDINATES["lon"]
        lat = PARIS_COORDINATES["lat"]
    else:
        geocode = await get_json(
            "https://api.geoapify.com/v1/geocode/search",
            {"text": destination, "apiKey": settings.geoapify_api_key, "limit": 1},
        )
        features = geocode.get("features") or []
        if not features:
            return {"source": "geoapify", "error": "Unable to geocode destination.", "places": fallback_places}
        props = features[0].get("properties") or {}
        lat = props.get("lat")
        lon = props.get("lon")
        if lat is None or lon is None:
            return {"source": "geoapify", "error": "Destination coordinates missing.", "places": fallback_places}

    data = await get_json(
        "https://api.geoapify.com/v2/places",
        {
            "categories": "tourism.sights,entertainment.museum",
            "filter": f"circle:{lon},{lat},5000",
            "limit": 20,
            "apiKey": settings.geoapify_api_key,
        },
    )
    if "error" in data:
        return {"source": "geoapify", "error": data["error"], "places": fallback_places}

    places = clean_geoapify_places(data.get("features") or [])
    if weather_risk == "bad":
        places = [place for place in places if "museum" in place["name"].lower()] + places
    return {"source": "geoapify", "places": places[:20] or fallback_places, "weather_adjusted": weather_risk == "bad"}
