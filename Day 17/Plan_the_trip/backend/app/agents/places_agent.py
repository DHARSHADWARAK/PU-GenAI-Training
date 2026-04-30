from typing import Any

from app.observability.langsmith import traceable
from app.state_schema import TripPlannerState
from app.tools.places_api import fetch_places


@traceable(name="Places Agent", run_type="tool")
async def places_agent(state: TripPlannerState) -> dict[str, Any]:
    prefs = state["trip_preferences"]
    weather_risk = state["weather_data"].get("risk", "unknown")
    places = await fetch_places(prefs.get("destination", ""), prefs.get("preferences", []), weather_risk)
    return {"places_data": places}
