"""API/tool layer for trip planning agents.

Agent to API mapping:
- Transport: OpenRouteService
- Weather: OpenWeatherMap
- Hotels: MakCorps
- Places: Geoapify
- Budget: Python
"""

from __future__ import annotations

import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from typing import Dict, List

import certifi


def get_weather(destination: str, days: int) -> Dict:
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        return _fallback_weather(destination, days, "OPENWEATHER_API_KEY missing")

    url = "https://api.openweathermap.org/data/2.5/forecast?" + urllib.parse.urlencode(
        {"q": f"{destination},IN", "appid": api_key, "units": "metric"}
    )
    try:
        data = _get_json(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return _fallback_weather(destination, days, f"OpenWeather request failed: {exc}")

    daily = {}
    for item in data.get("list", []):
        forecast_date = item.get("dt_txt", "").split(" ", 1)[0]
        if forecast_date:
            daily.setdefault(forecast_date, []).append(item)

    forecast = []
    for index, (forecast_date, entries) in enumerate(list(daily.items())[:days], start=1):
        temps = [entry.get("main", {}).get("temp") for entry in entries if entry.get("main")]
        conditions = [entry.get("weather", [{}])[0].get("description", "unknown") for entry in entries]
        rain_probability = max((entry.get("pop", 0) for entry in entries), default=0)
        forecast.append(
            {
                "day": index,
                "date": forecast_date,
                "condition": max(set(conditions), key=conditions.count) if conditions else "unknown",
                "temperature_c": round(sum(temps) / len(temps), 1) if temps else None,
                "rain_probability": round(rain_probability, 2),
            }
        )

    if not forecast:
        return _fallback_weather(destination, days, "OpenWeather returned no forecast rows")

    risk = "heavy_rain" if any(item["rain_probability"] >= 0.7 for item in forecast) else "normal"
    return {
        "source": "OpenWeatherMap API",
        "destination": data.get("city", {}).get("name", destination),
        "risk": risk,
        "forecast": forecast,
    }


def get_transport_options(source: str, destination: str, preference: str, travelers: int) -> Dict:
    route = _get_ors_route(source, destination)
    distance_km = route.get("distance_km") or _fallback_distance_km(source, destination)
    duration_hours = route.get("duration_hours") or round(distance_km / 55, 1)

    options = {
        "flight": {
            "mode": "flight",
            "summary": f"Approximate flight plan from {source} to {destination}; route distance reference {distance_km} km",
            "cost": max(4500, int(distance_km * 7)) * travelers,
            "duration": "1-3 hours plus airport time",
        },
        "train": {
            "mode": "train",
            "summary": f"Rail option from {source} to {destination}; route distance reference {distance_km} km",
            "cost": max(900, int(distance_km * 1.8)) * travelers,
            "duration": f"{max(3, round(distance_km / 65, 1))} hours estimated",
        },
        "car": {
            "mode": "car",
            "summary": f"Road route from {source} to {destination}: {distance_km} km, about {duration_hours} hours",
            "cost": max(3500, int(distance_km * 18)),
            "duration": f"{duration_hours} hours estimated",
        },
    }
    recommended = options.get(preference, options["car"])
    return {
        "source": route.get("source", "OpenRouteService fallback estimate"),
        "distance_km": distance_km,
        "duration_hours": duration_hours,
        "options": list(options.values()),
        "recommended": recommended,
        "api_error": route.get("api_error", ""),
    }


def recommend_hotels(destination: str, preference: str, budget: int, days: int, travelers: int, retry_count: int = 0) -> Dict:
    nights = max(days - 1, 1)
    checkin = date.today() + timedelta(days=30)
    checkout = checkin + timedelta(days=nights)
    api_hotels = _get_makcorps_hotels(destination, travelers, checkin, checkout)

    if api_hotels:
        selected = _select_hotel(api_hotels, budget, nights, retry_count)
        selected["category"] = "budget optimized" if retry_count else preference
        selected["nights"] = nights
        selected["source"] = "MakCorps API"
        alternatives = api_hotels[1:4]
        return {"selected": selected, "alternatives": alternatives, "checkin": str(checkin), "checkout": str(checkout)}

    per_night = min(3500, max(1800, budget // max(nights * 3, 1))) if retry_count else 5500
    selected = {
        "name": f"Smart Stay {destination}" if retry_count else f"Hotel {destination}",
        "category": "budget optimized" if retry_count else preference,
        "per_night": per_night,
        "nights": nights,
        "total_cost": per_night * nights,
        "rating": "not available",
        "features": ["API fallback estimate", "verify live availability before booking"],
        "source": "local fallback",
    }
    return {"selected": selected, "alternatives": _hotel_alternatives(destination, nights), "checkin": str(checkin), "checkout": str(checkout)}


def get_places(destination: str, interests: List[str], rainy: bool = False) -> Dict:
    api_places = _get_geoapify_places(destination, interests, rainy)
    if api_places:
        return {
            "source": "Geoapify Places API",
            "attractions": [place["name"] for place in api_places[:6]],
            "details": api_places[:6],
            "local_experiences": interests,
            "food": ["local restaurant search", "regional cuisine", "popular cafe", "street food area"],
            "safety_tips": ["Keep digital copies of IDs", "Use verified transport", "Avoid isolated areas late night"],
        }

    attractions = [f"{destination} heritage walk", f"{destination} local market", f"{destination} viewpoint"]
    if rainy:
        attractions.append("Indoor museum or cultural center")
    return {
        "source": "local fallback",
        "attractions": attractions,
        "details": [],
        "local_experiences": interests,
        "food": ["local restaurant", "regional cuisine", "popular cafe", "street food area"],
        "safety_tips": ["Keep digital copies of IDs", "Use verified transport", "Avoid isolated areas late night"],
    }


def estimate_budget(budget: int, days: int, travelers: int, transport: Dict, hotel: Dict, places: Dict) -> Dict:
    transport_cost = transport["recommended"]["cost"]
    hotel_cost = hotel["selected"]["total_cost"]
    optimized = hotel["selected"]["category"] == "budget optimized" and transport["recommended"]["mode"] == "train"
    food_rate = 800 if optimized else 1200
    transfer_rate = 500 if optimized else 900
    activity_rate = 600 if optimized else 1000
    buffer_rate = 0.05 if optimized else 0.1

    food_cost = food_rate * days * travelers
    local_transfer_cost = transfer_rate * days
    activities_cost = activity_rate * days
    buffer_cost = int(buffer_rate * (transport_cost + hotel_cost + food_cost + local_transfer_cost + activities_cost))
    total = transport_cost + hotel_cost + food_cost + local_transfer_cost + activities_cost + buffer_cost

    return {
        "source": "Python calculator",
        "user_budget": budget,
        "transport": transport_cost,
        "hotel": hotel_cost,
        "food": food_cost,
        "local_transfers": local_transfer_cost,
        "activities": activities_cost,
        "buffer": buffer_cost,
        "estimated_total": total,
        "status": "within budget" if total <= budget else "over budget",
        "optimization_tip": "Plan is feasible." if total <= budget else "Reduce hotel/transport/activity costs or increase budget.",
    }


def _get_ors_route(source: str, destination: str) -> Dict:
    api_key = os.getenv("OPENROUTESERVICE_API_KEY", "").strip()
    if not api_key:
        return {"api_error": "OPENROUTESERVICE_API_KEY missing"}

    start = _get_ors_coordinates(source, api_key)
    end = _get_ors_coordinates(destination, api_key)
    if not start or not end:
        return {"api_error": "ORS geocoding failed"}

    body = {"coordinates": [start, end]}
    try:
        data = _post_json("https://api.openrouteservice.org/v2/directions/driving-car", body, api_key)
        summary = data["routes"][0]["summary"]
        return {
            "source": "OpenRouteService Directions API",
            "distance_km": round(summary["distance"] / 1000, 1),
            "duration_hours": round(summary["duration"] / 3600, 1),
        }
    except (KeyError, IndexError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return {"api_error": f"ORS directions failed: {exc}"}


def _get_ors_coordinates(place: str, api_key: str) -> List[float]:
    url = "https://api.openrouteservice.org/geocode/search?" + urllib.parse.urlencode(
        {"api_key": api_key, "text": f"{place}, India", "size": 1}
    )
    try:
        data = _get_json(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return []
    features = data.get("features", [])
    return features[0].get("geometry", {}).get("coordinates", []) if features else []


def _get_makcorps_hotels(destination: str, travelers: int, checkin: date, checkout: date) -> List[Dict]:
    api_key = os.getenv("MAKCORPS_API_KEY", "").strip()
    if not api_key:
        return []

    city_id = _get_makcorps_city_id(destination, api_key)
    if not city_id:
        return []

    params = {
        "cityid": city_id,
        "pagination": 0,
        "cur": "INR",
        "rooms": 1,
        "adults": max(1, travelers),
        "checkin": str(checkin),
        "checkout": str(checkout),
        "api_key": api_key,
    }
    try:
        data = _get_json("https://api.makcorps.com/city?" + urllib.parse.urlencode(params))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return []

    hotels = data if isinstance(data, list) else data.get("hotels", data.get("data", [])) if isinstance(data, dict) else []
    parsed = []
    for item in hotels:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("hotelName") or item.get("hotel_name")
        if not name:
            continue
        price = _extract_price(item)
        parsed.append(
            {
                "name": name,
                "per_night": price,
                "total_cost": price * max((checkout - checkin).days, 1),
                "rating": item.get("rating") or item.get("reviewScore") or "not available",
                "hotel_id": item.get("hotelId") or item.get("hotelid") or item.get("document_id"),
                "features": ["MakCorps hotel result", "compare vendors before booking"],
                "source": "MakCorps API",
            }
        )
    return sorted(parsed, key=lambda hotel: hotel["total_cost"])


def _get_makcorps_city_id(destination: str, api_key: str) -> str:
    params = {"api_key": api_key, "name": destination}
    try:
        data = _get_json("https://api.makcorps.com/mapping?" + urllib.parse.urlencode(params))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return ""
    for item in data if isinstance(data, list) else []:
        if item.get("type") == "GEO":
            return str(item.get("document_id") or item.get("value") or "")
    return ""


def _get_geoapify_places(destination: str, interests: List[str], rainy: bool) -> List[Dict]:
    api_key = os.getenv("GEOAPIFY_API_KEY", "").strip()
    if not api_key:
        return []

    coords = _get_geoapify_coordinates(destination, api_key)
    if not coords:
        return []
    lon, lat = coords
    categories = ["tourism", "tourism.sights", "entertainment", "leisure"]
    if rainy:
        categories = ["entertainment.museum", "tourism.sights", "entertainment.culture"]
    if any("nightlife" in item for item in interests):
        categories.append("entertainment.nightclub")

    params = {
        "categories": ",".join(categories),
        "filter": f"circle:{lon},{lat},10000",
        "bias": f"proximity:{lon},{lat}",
        "limit": 12,
        "apiKey": api_key,
    }
    try:
        data = _get_json("https://api.geoapify.com/v2/places?" + urllib.parse.urlencode(params))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return []

    places = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        name = props.get("name")
        if not name:
            continue
        places.append(
            {
                "name": name,
                "address": props.get("formatted", ""),
                "categories": props.get("categories", []),
                "distance_m": props.get("distance"),
            }
        )
    return places


def _get_geoapify_coordinates(destination: str, api_key: str) -> List[float]:
    params = {"text": f"{destination}, India", "limit": 1, "apiKey": api_key}
    try:
        data = _get_json("https://api.geoapify.com/v1/geocode/search?" + urllib.parse.urlencode(params))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return []
    features = data.get("features", [])
    if not features:
        return []
    props = features[0].get("properties", {})
    return [props.get("lon"), props.get("lat")] if props.get("lon") and props.get("lat") else []


def _select_hotel(hotels: List[Dict], budget: int, nights: int, retry_count: int) -> Dict:
    if retry_count:
        affordable = [hotel for hotel in hotels if hotel["total_cost"] <= max(budget * 0.4, 1)]
        return dict(affordable[0] if affordable else hotels[0])
    return dict(hotels[0])


def _extract_price(item: Dict) -> int:
    candidates = [item.get("price"), item.get("price1"), item.get("minPrice"), item.get("rate")]
    for candidate in candidates:
        if candidate is None:
            continue
        digits = re.sub(r"[^0-9.]", "", str(candidate))
        if digits:
            return max(1000, int(float(digits)))
    return 3500


def _hotel_alternatives(destination: str, nights: int) -> List[Dict]:
    return [
        {"name": f"City Inn {destination}", "total_cost": 2800 * nights, "source": "local fallback"},
        {"name": f"Local Homestay {destination}", "total_cost": 2200 * nights, "source": "local fallback"},
    ]


def _fallback_weather(destination: str, days: int, reason: str) -> Dict:
    forecast = [
        {"day": day, "condition": "Light clouds with warm evenings", "temperature_c": 28, "rain_probability": 0.2}
        for day in range(1, days + 1)
    ]
    return {"source": "local fallback", "reason": reason, "destination": destination, "risk": "normal", "forecast": forecast}


def _fallback_distance_km(source: str, destination: str) -> int:
    known = {
        ("bangalore", "goa"): 560,
        ("bangalore", "hyderabad"): 575,
        ("bangalore", "nellore"): 380,
        ("bangalore", "chennai"): 350,
    }
    return known.get((source.lower(), destination.lower()), 500)


def _get_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "trip-planner-langgraph/1.0"})
    with urllib.request.urlopen(request, timeout=20, context=_ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, body: Dict, api_key: str):
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": api_key, "Content-Type": "application/json", "User-Agent": "trip-planner-langgraph/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20, context=_ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def _ssl_context():
    return ssl.create_default_context(cafile=certifi.where())
