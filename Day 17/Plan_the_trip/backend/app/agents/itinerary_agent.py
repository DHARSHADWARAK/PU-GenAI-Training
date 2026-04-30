from typing import Any

from app.observability.langsmith import traceable
from app.services.llm_service import LLMService
from app.state_schema import TripPlannerState

llm_service = LLMService()


@traceable(name="Itinerary Agent", run_type="chain")
async def itinerary_agent(state: TripPlannerState) -> dict[str, Any]:
    itinerary = await llm_service.generate_itinerary(
        {
            "user_profile": state["user_profile"],
            "trip_preferences": state["trip_preferences"],
            "weather_data": state["weather_data"],
            "hotel_data": state["hotel_data"],
            "transport_data": state["transport_data"],
            "places_data": state["places_data"],
            "budget_summary": state["budget_summary"],
        }
    )
    return {"itinerary": itinerary}
