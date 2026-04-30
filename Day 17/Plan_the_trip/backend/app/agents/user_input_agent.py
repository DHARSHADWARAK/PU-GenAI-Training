from datetime import date, timedelta
from typing import Any

from app.observability.langsmith import traceable
from app.state_schema import TripPlannerState
from app.utils.dates import date_range


REQUIRED_FIELDS = ["source", "destination", "start_date", "end_date", "budget"]


@traceable(name="User Input Agent", run_type="chain")
async def user_input_agent(state: TripPlannerState) -> dict[str, Any]:
    raw = state["user_profile"].get("raw_request", {})
    missing = [field for field in REQUIRED_FIELDS if raw.get(field) in (None, "", [])]
    start = raw.get("start_date") or (date.today() + timedelta(days=14)).isoformat()
    end = raw.get("end_date") or (date.today() + timedelta(days=17)).isoformat()
    dates = date_range(start, end)
    trip_preferences = {
        "source": raw.get("source", "Current city"),
        "destination": raw.get("destination", "Selected destination"),
        "start_date": dates[0].isoformat(),
        "end_date": dates[-1].isoformat(),
        "date_list": [d.isoformat() for d in dates],
        "budget": float(raw.get("budget") or 50000),
        "currency": raw.get("currency", "INR"),
        "travellers": int(raw.get("travellers") or 1),
        "preferences": raw.get("preferences") or [],
        "pace": raw.get("pace", "balanced"),
    }
    decision = dict(state["orchestrator_decision"])
    decision["missing_fields"] = missing
    decision["stage"] = "input_normalized"
    if missing:
        decision.setdefault("warnings", []).append(f"Missing fields defaulted: {', '.join(missing)}")
    return {"trip_preferences": trip_preferences, "orchestrator_decision": decision}
