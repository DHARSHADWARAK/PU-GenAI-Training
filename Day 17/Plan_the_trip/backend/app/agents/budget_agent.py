from typing import Any

from app.observability.langsmith import traceable
from app.state_schema import TripPlannerState


@traceable(name="Budget Agent", run_type="chain")
async def budget_agent(state: TripPlannerState) -> dict[str, Any]:
    prefs = state["trip_preferences"]
    budget = float(prefs.get("budget", 0))
    days = max(len(prefs.get("date_list", [])), 1)
    travellers = max(int(prefs.get("travellers", 1)), 1)
    hotel = state["hotel_data"].get("selected") or {}
    hotel_total = float(hotel.get("price_per_night") or budget * 0.25 / days) * max(days - 1, 1)
    transport_total = float(state["transport_data"].get("estimated_cost") or budget * 0.2)
    activity_total = days * travellers * 2500
    food_total = days * travellers * 1800
    contingency = budget * 0.1
    total = hotel_total + transport_total + activity_total + food_total + contingency
    return {
        "budget_summary": {
            "currency": prefs.get("currency", "INR"),
            "total_budget": round(budget, 2),
            "hotel": round(hotel_total, 2),
            "transport": round(transport_total, 2),
            "activities": round(activity_total, 2),
            "food": round(food_total, 2),
            "contingency": round(contingency, 2),
            "estimated_total": round(total, 2),
            "remaining": round(budget - total, 2),
            "status": "over_budget" if total > budget else "within_budget",
        }
    }
