from typing import Any

from app.observability.langsmith import traceable
from app.state_schema import TripPlannerState
from app.tools.hotel_api import fetch_hotels


@traceable(name="Hotel Agent", run_type="tool")
async def hotel_agent(state: TripPlannerState) -> dict[str, Any]:
    prefs = state["trip_preferences"]
    hotels = await fetch_hotels(
        prefs.get("destination", ""),
        float(prefs.get("budget", 0)),
        int(prefs.get("travellers", 1)),
    )
    return {"hotel_data": hotels}
