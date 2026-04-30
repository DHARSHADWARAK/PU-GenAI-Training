from typing import Any

from app.config import get_settings
from app.observability.langsmith import traceable
from app.state_schema import TripPlannerState


@traceable(name="Orchestrator Agent", run_type="chain")
async def orchestrator_agent(state: TripPlannerState) -> dict[str, Any]:
    decision = dict(state["orchestrator_decision"])
    decision["stage"] = "orchestrating"
    decision["required_agents"] = [
        "user_input",
        "memory",
        "weather",
        "transport",
        "hotel",
        "places",
        "budget",
        "itinerary",
        "final_review",
        "pdf_generator",
    ]
    return {"orchestrator_decision": decision}


@traceable(name="Orchestrator Decision", run_type="chain")
async def orchestrator_decision_agent(state: TripPlannerState) -> dict[str, Any]:
    decision = dict(state["orchestrator_decision"])
    decision["stage"] = "parallel_agents_requested"
    decision["parallel_agents"] = ["weather", "transport", "hotel", "places", "budget", "itinerary"]
    return {"orchestrator_decision": decision}


@traceable(name="Orchestrator Validation", run_type="chain")
async def orchestrator_validation_agent(state: TripPlannerState) -> dict[str, Any]:
    settings = get_settings()
    decision = dict(state["orchestrator_decision"])
    review = state["review_status"]
    decision["stage"] = "validated"
    decision["approved"] = bool(review.get("approved"))
    decision["retry_agents"] = review.get("retry_agents", [])
    if not decision["approved"]:
        decision["retry_count"] = int(decision.get("retry_count", 0)) + 1
        if decision["retry_count"] > settings.max_agent_retries:
            decision["approved"] = True
            decision.setdefault("warnings", []).append("Approved after max retries with remaining review issues documented.")
    return {"orchestrator_decision": decision}


def route_after_validation(state: TripPlannerState) -> str:
    return "approved" if state["orchestrator_decision"].get("approved") else "retry"
