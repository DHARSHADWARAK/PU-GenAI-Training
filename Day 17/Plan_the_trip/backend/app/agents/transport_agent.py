from typing import Any

from app.observability.langsmith import traceable
from app.state_schema import TripPlannerState
from app.tools.transport_api import fetch_transport


@traceable(name="Transport Agent", run_type="tool")
async def transport_agent(state: TripPlannerState) -> dict[str, Any]:
    prefs = state["trip_preferences"]
    transport = await fetch_transport(
        prefs.get("source", ""),
        prefs.get("destination", ""),
        prefs.get("start_date"),
        int(prefs.get("travellers", 1)),
    )
    return {"transport_data": transport}
