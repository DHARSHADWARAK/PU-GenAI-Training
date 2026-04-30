import asyncio
from typing import Any

from app.agents.budget_agent import budget_agent
from app.agents.hotel_agent import hotel_agent
from app.agents.itinerary_agent import itinerary_agent
from app.agents.places_agent import places_agent
from app.agents.transport_agent import transport_agent
from app.agents.weather_agent import weather_agent
from app.observability.langsmith import traceable
from app.state_schema import TripPlannerState


@traceable(name="Parallel Agent Runner", run_type="chain")
async def parallel_agents_runner(state: TripPlannerState) -> dict[str, Any]:
    weather_result, transport_result, hotel_result = await asyncio.gather(
        weather_agent(state),
        transport_agent(state),
        hotel_agent(state),
    )
    enriched_state: TripPlannerState = {
        **state,
        **weather_result,
        **transport_result,
        **hotel_result,
    }
    places_result = await places_agent(enriched_state)
    enriched_state = {**enriched_state, **places_result}
    budget_result = await budget_agent(enriched_state)
    enriched_state = {**enriched_state, **budget_result}
    itinerary_result = await itinerary_agent(enriched_state)
    decision = dict(state["orchestrator_decision"])
    decision["stage"] = "parallel_agents_completed"
    decision["parallel_execution"] = {
        "concurrent": ["weather", "transport", "hotel"],
        "weather_dependent": ["places"],
        "cost_dependent": ["budget"],
        "plan_dependent": ["itinerary"],
    }
    return {
        **weather_result,
        **transport_result,
        **hotel_result,
        **places_result,
        **budget_result,
        **itinerary_result,
        "orchestrator_decision": decision,
    }
