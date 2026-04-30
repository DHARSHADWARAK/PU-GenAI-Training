"""LangGraph multi-agent workflow for the trip planner."""

from __future__ import annotations

from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from agents import (
    budget_agent,
    final_response_agent,
    final_review_agent,
    hotel_agent,
    itinerary_agent,
    memory_retrieval_agent,
    memory_update_agent,
    orchestrator_start_agent,
    orchestrator_validation_agent,
    pdf_generator_agent,
    places_agent,
    transport_agent,
    user_input_agent,
    weather_agent,
)


class TripPlannerState(TypedDict):
    user_query: str
    user_profile: Dict[str, Any]
    trip_preferences: Dict[str, Any]
    weather_data: Dict[str, Any]
    hotel_data: Dict[str, Any]
    transport_data: Dict[str, Any]
    places_data: Dict[str, Any]
    budget_summary: Dict[str, Any]
    itinerary: Dict[str, Any]
    review_status: Dict[str, Any]
    pdf_status: Dict[str, Any]
    orchestrator_decision: Dict[str, Any]
    memory: Dict[str, Any]
    final_answer: str
    trace: List[str]


def initial_state(user_query: str) -> TripPlannerState:
    return {
        "user_query": user_query,
        "user_profile": {},
        "trip_preferences": {},
        "weather_data": {},
        "hotel_data": {},
        "transport_data": {},
        "places_data": {},
        "budget_summary": {},
        "itinerary": {},
        "review_status": {},
        "pdf_status": {},
        "orchestrator_decision": {},
        "memory": {},
        "final_answer": "",
        "trace": [],
    }


def _needs_retry(state: TripPlannerState) -> str:
    if state["orchestrator_decision"].get("retry_hotel"):
        return "retry_hotel"
    if state["orchestrator_decision"].get("retry_transport"):
        return "retry_transport"
    return "approved"


def build_trip_planner_graph():
    graph = StateGraph(TripPlannerState)

    graph.add_node("orchestrator_start", orchestrator_start_agent)
    graph.add_node("user_input", user_input_agent)
    graph.add_node("memory_retrieval", memory_retrieval_agent)
    graph.add_node("weather", weather_agent)
    graph.add_node("transport", transport_agent)
    graph.add_node("hotel", hotel_agent)
    graph.add_node("places", places_agent)
    graph.add_node("budget", budget_agent)
    graph.add_node("itinerary", itinerary_agent)
    graph.add_node("final_review", final_review_agent)
    graph.add_node("orchestrator_validation", orchestrator_validation_agent)
    graph.add_node("memory_update", memory_update_agent)
    graph.add_node("pdf_generator", pdf_generator_agent)
    graph.add_node("final_response", final_response_agent)

    graph.set_entry_point("orchestrator_start")
    graph.add_edge("orchestrator_start", "user_input")
    graph.add_edge("user_input", "memory_retrieval")
    graph.add_edge("memory_retrieval", "weather")
    graph.add_edge("weather", "transport")
    graph.add_edge("transport", "hotel")
    graph.add_edge("hotel", "places")
    graph.add_edge("places", "budget")
    graph.add_edge("budget", "itinerary")
    graph.add_edge("itinerary", "final_review")
    graph.add_edge("final_review", "orchestrator_validation")
    graph.add_conditional_edges(
        "orchestrator_validation",
        _needs_retry,
        {
            "retry_hotel": "hotel",
            "retry_transport": "transport",
            "approved": "memory_update",
        },
    )
    graph.add_edge("memory_update", "pdf_generator")
    graph.add_edge("pdf_generator", "final_response")
    graph.add_edge("final_response", END)

    return graph.compile()
