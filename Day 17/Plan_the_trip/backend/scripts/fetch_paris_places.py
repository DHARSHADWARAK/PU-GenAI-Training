import os
from pprint import pprint
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

URL = "https://api.geoapify.com/v2/places"
INCLUDED_CATEGORIES = {
    "tourism.sights",
    "tourism.attraction",
    "entertainment.museum",
}
EXCLUDED_PRIMARY_CATEGORIES = (
    "commercial",
    "catering.restaurant",
)


def is_relevant_tourist_place(categories: list[str]) -> bool:
    if not categories:
        return False
    primary_category = categories[0]
    if primary_category.startswith(EXCLUDED_PRIMARY_CATEGORIES):
        return False
    return any(category in INCLUDED_CATEGORIES for category in categories)


def clean_place(feature: dict[str, Any]) -> dict[str, Any] | None:
    properties = feature.get("properties") or {}
    categories = properties.get("categories") or []
    if not is_relevant_tourist_place(categories):
        return None

    name = properties.get("name")
    lat = properties.get("lat")
    lon = properties.get("lon")
    if not name or lat is None or lon is None:
        return None

    return {
        "name": name,
        "address": properties.get("formatted") or "",
        "lat": lat,
        "lon": lon,
    }


def fetch_paris_places() -> list[dict[str, Any]]:
    api_key = os.getenv("GEOAPIFY_API_KEY")
    if not api_key:
        print("Missing GEOAPIFY_API_KEY in environment")
        return []

    params = {
        "categories": "tourism.sights,entertainment.museum",
        "filter": "circle:2.3522,48.8566,5000",
        "limit": 20,
        "apiKey": api_key,
    }

    try:
        response = requests.get(url=URL, params=params, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        status_code = getattr(exc.response, "status_code", "no status")
        print(f"Geoapify API failed: {status_code} - {exc}")
        return []

    data = response.json()
    features = data.get("features") or []
    cleaned_places = []
    for feature in features:
        place = clean_place(feature)
        if place:
            cleaned_places.append(place)
    return cleaned_places


if __name__ == "__main__":
    pprint(fetch_paris_places())
