from typing import Any, TypedDict


class TripPlannerState(TypedDict):
    user_profile: dict[str, Any]
    trip_preferences: dict[str, Any]
    weather_data: dict[str, Any]
    hotel_data: dict[str, Any]
    transport_data: dict[str, Any]
    places_data: dict[str, Any]
    budget_summary: dict[str, Any]
    itinerary: dict[str, Any]
    review_status: dict[str, Any]
    pdf_status: dict[str, Any]
    orchestrator_decision: dict[str, Any]


def initial_state(payload: dict[str, Any]) -> TripPlannerState:
    return {
        "user_profile": {
            "user_id": payload.get("user_id", "anonymous"),
            "name": payload.get("name"),
            "email": payload.get("email"),
            "raw_request": payload,
        },
        "trip_preferences": {},
        "weather_data": {},
        "hotel_data": {},
        "transport_data": {},
        "places_data": {},
        "budget_summary": {},
        "itinerary": {},
        "review_status": {},
        "pdf_status": {},
        "orchestrator_decision": {
            "stage": "received",
            "retry_count": 0,
            "required_agents": [],
            "errors": [],
            "missing_fields": [],
            "approved": False,
        },
    }
