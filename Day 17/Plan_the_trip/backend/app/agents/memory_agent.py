import json
from typing import Any

from app.memory.session_store import session_store
from app.memory.vector_store import vector_store
from app.observability.langsmith import traceable
from app.state_schema import TripPlannerState


@traceable(name="Memory Retrieval Agent", run_type="retriever")
async def retrieve_memory_agent(state: TripPlannerState) -> dict[str, Any]:
    user_id = state["user_profile"].get("user_id", "anonymous")
    query = json.dumps(state["trip_preferences"], default=str)
    past_trips = vector_store.search(user_id, query)
    session = session_store.get(user_id)
    profile = dict(state["user_profile"])
    profile["memory"] = {"past_trips": [item["trip"] for item in past_trips], "session": session}
    decision = dict(state["orchestrator_decision"])
    decision["stage"] = "memory_retrieved"
    return {"user_profile": profile, "orchestrator_decision": decision}


@traceable(name="Memory Update Agent", run_type="chain")
async def update_memory_agent(state: TripPlannerState) -> dict[str, Any]:
    user_id = state["user_profile"].get("user_id", "anonymous")
    trip_record = {
        "trip_preferences": state["trip_preferences"],
        "hotel_data": state["hotel_data"],
        "budget_summary": state["budget_summary"],
        "itinerary": state["itinerary"],
    }
    vector_store.add_trip(user_id, trip_record)
    session_store.update(user_id, {"last_trip": trip_record, "preferences": state["trip_preferences"].get("preferences", [])})
    decision = dict(state["orchestrator_decision"])
    decision["stage"] = "memory_updated"
    return {"orchestrator_decision": decision}
