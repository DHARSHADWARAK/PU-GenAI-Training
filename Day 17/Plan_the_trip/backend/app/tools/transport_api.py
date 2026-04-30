import asyncio
import logging
import random
import re
from typing import Any

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

AVIATIONSTACK_FLIGHTS_URL = "http://api.aviationstack.com/v1/flights"

CITY_TO_IATA = {
    "amsterdam": "AMS",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "berlin": "BER",
    "chennai": "MAA",
    "delhi": "DEL",
    "dubai": "DXB",
    "goa": "GOI",
    "hyderabad": "HYD",
    "istanbul": "IST",
    "jaipur": "JAI",
    "kolkata": "CCU",
    "london": "LHR",
    "los angeles": "LAX",
    "mumbai": "BOM",
    "new delhi": "DEL",
    "new york": "JFK",
    "paris": "CDG",
    "rome": "FCO",
    "san francisco": "SFO",
    "singapore": "SIN",
    "sydney": "SYD",
    "tokyo": "HND",
    "toronto": "YYZ",
}


def get_iata_code(city: str | None) -> str | None:
    if not city:
        return None
    normalized = city.strip().lower()
    return CITY_TO_IATA.get(normalized)


def _fallback_transport(source: str, destination: str, reason: str) -> dict[str, Any]:
    safe_reason = _sanitize_error(reason)
    return {
        "source": source,
        "destination": destination,
        "provider": "fallback",
        "mode": "flight",
        "flights": [],
        "estimated_cost": 0,
        "summary": f"No live flight data available: {safe_reason}",
        "error": safe_reason,
    }


def _sanitize_error(message: str) -> str:
    return re.sub(r"(access_key=)[^&\\s]+", r"\1***", str(message))


def _mock_price(dep_iata: str, arr_iata: str, travellers: int) -> int:
    seed = f"{dep_iata}-{arr_iata}-{travellers}"
    rng = random.Random(seed)
    return rng.randint(6500, 28000) * max(travellers, 1)


def _parse_flight(item: dict[str, Any], travellers: int) -> dict[str, Any]:
    airline = item.get("airline") or {}
    flight = item.get("flight") or {}
    departure = item.get("departure") or {}
    arrival = item.get("arrival") or {}
    dep_iata = departure.get("iata") or ""
    arr_iata = arrival.get("iata") or ""
    flight_number = flight.get("iata") or flight.get("number") or "N/A"
    return {
        "airline": airline.get("name") or "Unknown airline",
        "flight_number": flight_number,
        "departure_airport": departure.get("airport") or dep_iata or "Unknown departure airport",
        "arrival_airport": arrival.get("airport") or arr_iata or "Unknown arrival airport",
        "departure_time": departure.get("scheduled") or departure.get("estimated") or "",
        "arrival_time": arrival.get("scheduled") or arrival.get("estimated") or "",
        "status": item.get("flight_status") or "unknown",
        "mock_price": _mock_price(dep_iata, arr_iata, travellers),
    }


def _fetch_aviationstack_flights(
    access_key: str,
    dep_iata: str,
    arr_iata: str,
    departure_date: str | None,
    travellers: int,
    timeout: float,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "access_key": access_key,
        "dep_iata": dep_iata,
        "arr_iata": arr_iata,
        "limit": 5,
    }
    if departure_date:
        params["flight_date"] = departure_date

    response = requests.get(AVIATIONSTACK_FLIGHTS_URL, params=params, timeout=timeout)
    if response.status_code >= 400:
        raise requests.HTTPError(f"{response.status_code} - {response.text}", response=response)

    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))

    flights = []
    for item in payload.get("data", [])[:5]:
        flights.append(_parse_flight(item, travellers))
    return flights


async def fetch_transport(
    source: str,
    destination: str,
    departure_date: str | None = None,
    travellers: int = 1,
) -> dict[str, Any]:
    settings = get_settings()
    dep_iata = get_iata_code(source)
    arr_iata = get_iata_code(destination)
    if not dep_iata or not arr_iata:
        return _fallback_transport(source, destination, "Unsupported source or destination city IATA mapping.")

    if not settings.aviationstack_api_key:
        return _fallback_transport(source, destination, "Missing AVIATIONSTACK_API_KEY.")

    try:
        flights = await asyncio.to_thread(
            _fetch_aviationstack_flights,
            settings.aviationstack_api_key,
            dep_iata,
            arr_iata,
            departure_date,
            max(int(travellers or 1), 1),
            settings.request_timeout_seconds,
        )
    except Exception as exc:
        logger.warning("Aviationstack flight lookup failed for %s to %s: %s", dep_iata, arr_iata, _sanitize_error(str(exc)))
        return _fallback_transport(source, destination, str(exc))

    estimated_cost = min((flight["mock_price"] for flight in flights), default=0)
    summary = (
        f"Found {len(flights)} flights from {dep_iata} to {arr_iata}."
        if flights
        else f"No flights returned from {dep_iata} to {arr_iata}."
    )
    return {
        "source": source,
        "destination": destination,
        "provider": "aviationstack",
        "mode": "flight",
        "dep_iata": dep_iata,
        "arr_iata": arr_iata,
        "departure_date": departure_date,
        "travellers": travellers,
        "flights": flights[:5],
        "estimated_cost": estimated_cost,
        "summary": summary,
    }
