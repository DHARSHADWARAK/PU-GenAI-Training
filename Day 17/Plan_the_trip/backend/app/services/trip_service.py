from typing import Any

from app.config import get_settings
from app.graph.trip_graph import trip_graph
from app.observability.langsmith import flush_traces, traceable, tracing_context
from app.state_schema import initial_state


@traceable(name="plan_trip_request", run_type="chain")
async def plan_trip(payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    state = initial_state(payload)
    metadata = {
        "user_id": payload.get("user_id", "anonymous"),
        "source": payload.get("source"),
        "destination": payload.get("destination"),
        "start_date": payload.get("start_date"),
        "end_date": payload.get("end_date"),
    }
    try:
        with tracing_context(settings, metadata=metadata):
            result = await trip_graph.ainvoke(
                state,
                config={
                    "run_name": "ai_trip_planner_graph",
                    "tags": ["trip-planner", "langgraph", settings.app_env],
                    "metadata": metadata,
                },
            )
    finally:
        flush_traces(settings)
    return {
        "user_profile": result["user_profile"],
        "trip_preferences": result["trip_preferences"],
        "weather_data": result["weather_data"],
        "hotel_data": result["hotel_data"],
        "transport_data": result["transport_data"],
        "places_data": result["places_data"],
        "budget_summary": result["budget_summary"],
        "itinerary": result["itinerary"],
        "review_status": result["review_status"],
        "pdf_status": result["pdf_status"],
        "orchestrator_decision": result["orchestrator_decision"],
        "pdf_link": result["pdf_status"].get("url"),
    }
