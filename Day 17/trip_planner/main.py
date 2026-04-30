"""Multi-Agent Trip Planner using LangGraph.

Run:
    python main.py
"""

from __future__ import annotations

from dotenv import load_dotenv

from workflow import build_trip_planner_graph, initial_state


def run_trip_request(user_query: str) -> None:
    load_dotenv()
    graph = build_trip_planner_graph()
    state = initial_state(user_query)

    print("=" * 90)
    print(f"User: {user_query}")
    print("=" * 90)

    final_state = state
    for event in graph.stream(state):
        node_name, node_state = next(iter(event.items()))
        final_state = node_state
        _print_trace(node_name, node_state)

    print("\nFinal Answer:\n")
    print(final_state["final_answer"])
    print(f"\nPDF Report: {final_state['pdf_status'].get('path', 'not generated')}")


def _print_trace(node_name: str, state: dict) -> None:
    labels = {
        "orchestrator_start": "[Orchestrator Agent]",
        "user_input": "[User Input Agent]",
        "memory_retrieval": "[Memory Agent]",
        "weather": "[Weather Agent]",
        "transport": "[Transport Agent]",
        "hotel": "[Hotel Agent]",
        "places": "[Places Explorer Agent]",
        "budget": "[Budget Agent]",
        "itinerary": "[Itinerary Agent]",
        "final_review": "[Final Review Agent]",
        "orchestrator_validation": "[Orchestrator Agent]",
        "memory_update": "[Memory Agent]",
        "pdf_generator": "[PDF Generator Agent]",
        "final_response": "[Orchestrator Agent]",
    }
    label = labels.get(node_name, f"[{node_name}]")

    if node_name == "orchestrator_start":
        print(f"{label} Understanding user goal...")
        print(f"{label} Planned agent order: {state['orchestrator_decision'].get('agent_plan')}")
    elif node_name == "user_input":
        print(f"{label} Extracted preferences: {state['trip_preferences']}")
        if state["orchestrator_decision"].get("missing_info"):
            print(f"{label} Missing info filled with defaults: {state['orchestrator_decision']['missing_info']}")
    elif node_name == "memory_retrieval":
        print(f"{label} Retrieved past preferences: {state['memory'].get('retrieved_preferences')}")
    elif node_name in {"weather", "transport", "hotel", "places", "budget", "itinerary", "final_review"}:
        key = {
            "weather": "weather_data",
            "transport": "transport_data",
            "hotel": "hotel_data",
            "places": "places_data",
            "budget": "budget_summary",
            "itinerary": "itinerary",
            "final_review": "review_status",
        }[node_name]
        print(f"{label} Completed. Result: {state[key]}")
    elif node_name == "orchestrator_validation":
        decision = state["orchestrator_decision"]
        print(f"{label} Validating final plan...")
        print(f"{label} Approved: {decision.get('approved')} | Retries: {decision.get('retries')}")
    elif node_name == "memory_update":
        print(f"{label} Updated trip memory at {state['memory'].get('memory_file')}")
    elif node_name == "pdf_generator":
        print(f"{label} Generated PDF: {state['pdf_status'].get('path')}")
    elif node_name == "final_response":
        print(f"{label} Final response ready.")


def main() -> None:
    load_dotenv()
    print("Multi-Agent Trip Planner using LangGraph")
    print("Type 'exit' to stop.\n")

    while True:
        query = input("Trip request: ").strip()
        if query.lower() in {"exit", "quit"}:
            break
        if not query:
            continue
        run_trip_request(query)
        print("\n" + "-" * 90 + "\n")


if __name__ == "__main__":
    main()
