from typing import Any

from app.observability.langsmith import traceable
from app.state_schema import TripPlannerState
from app.tools.weather_api import fetch_weather


@traceable(name="Weather Agent", run_type="tool")
async def weather_agent(state: TripPlannerState) -> dict[str, Any]:
    destination = state["trip_preferences"].get("destination", "")
    weather = await fetch_weather(destination)
    return {"weather_data": weather}
