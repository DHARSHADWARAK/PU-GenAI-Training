from langgraph.graph import END, START, StateGraph

from app.agents.final_review_agent import final_review_agent
from app.agents.memory_agent import retrieve_memory_agent, update_memory_agent
from app.agents.parallel_agents import parallel_agents_runner
from app.agents.pdf_generator_agent import pdf_generator_agent
from app.agents.user_input_agent import user_input_agent
from app.orchestrator.supervisor import (
    orchestrator_agent,
    orchestrator_decision_agent,
    orchestrator_validation_agent,
    route_after_validation,
)
from app.state_schema import TripPlannerState


def build_trip_graph():
    graph = StateGraph(TripPlannerState)
    graph.add_node("orchestrator", orchestrator_agent)
    graph.add_node("user_input", user_input_agent)
    graph.add_node("memory_retrieval", retrieve_memory_agent)
    graph.add_node("orchestrator_decision", orchestrator_decision_agent)
    graph.add_node("parallel_agents", parallel_agents_runner)
    graph.add_node("final_review", final_review_agent)
    graph.add_node("orchestrator_validation", orchestrator_validation_agent)
    graph.add_node("memory_update", update_memory_agent)
    graph.add_node("pdf_generator", pdf_generator_agent)

    graph.add_edge(START, "orchestrator")
    graph.add_edge("orchestrator", "user_input")
    graph.add_edge("user_input", "memory_retrieval")
    graph.add_edge("memory_retrieval", "orchestrator_decision")

    graph.add_edge("orchestrator_decision", "parallel_agents")
    graph.add_edge("parallel_agents", "final_review")
    graph.add_edge("final_review", "orchestrator_validation")

    graph.add_conditional_edges(
        "orchestrator_validation",
        route_after_validation,
        {"approved": "memory_update", "retry": "orchestrator_decision"},
    )
    graph.add_edge("memory_update", "pdf_generator")
    graph.add_edge("pdf_generator", END)
    return graph.compile()


trip_graph = build_trip_graph()
