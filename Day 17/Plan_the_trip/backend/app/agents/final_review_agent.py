from typing import Any

from app.observability.langsmith import traceable
from app.state_schema import TripPlannerState


@traceable(name="Final Review Agent", run_type="chain")
async def final_review_agent(state: TripPlannerState) -> dict[str, Any]:
    issues: list[str] = []
    retry_agents: list[str] = []
    budget = state["budget_summary"]
    hotel = state["hotel_data"].get("selected") or {}
    days = max(len(state["trip_preferences"].get("date_list", [])), 1)
    hotel_total = float(hotel.get("price_per_night") or 0) * max(days - 1, 1)
    if budget.get("status") == "over_budget":
        issues.append("Estimated trip cost exceeds budget.")
        retry_agents.extend(["hotel", "budget"])
    if hotel_total > float(state["trip_preferences"].get("budget", 0)) * 0.45:
        issues.append("Hotel selection consumes too much of the budget.")
        retry_agents.extend(["hotel", "budget"])
    if state["weather_data"].get("risk") == "bad" and not state["places_data"].get("weather_adjusted"):
        issues.append("Bad weather requires indoor or weather-safe places.")
        retry_agents.append("places")
    if not state["itinerary"].get("days"):
        issues.append("Itinerary is missing day-wise details.")
        retry_agents.append("itinerary")
    approved = not issues
    return {
        "review_status": {
            "approved": approved,
            "issues": issues,
            "retry_agents": sorted(set(retry_agents)),
            "quality_score": 92 if approved else 65,
        }
    }
