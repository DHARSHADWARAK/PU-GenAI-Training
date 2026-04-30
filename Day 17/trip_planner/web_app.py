"""FastAPI frontend for the LangGraph trip planner.

Run:
    uvicorn web_app:app --reload
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from workflow import build_trip_planner_graph, initial_state


BASE_DIR = Path(__file__).parent
REPORTS_DIR = BASE_DIR / "reports"

app = FastAPI(title="Multi-Agent Trip Planner")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


SAMPLE_QUERY = (
    "Plan a 5-day Goa trip from Bangalore for a couple. Budget: 30000. "
    "Need beach resort, nightlife, sightseeing, seafood, flight preferred."
)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "sample_query": SAMPLE_QUERY,
            "result": None,
        },
    )


@app.post("/plan")
def plan_trip(request: Request, trip_request: str = Form(...)):
    result = run_planner(trip_request)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "sample_query": SAMPLE_QUERY,
            "result": result,
        },
    )


@app.get("/download/{filename}")
def download_report(filename: str):
    path = (REPORTS_DIR / filename).resolve()
    if REPORTS_DIR.resolve() not in path.parents and path != REPORTS_DIR.resolve():
        return FileResponse(REPORTS_DIR / "missing.pdf", filename="missing.pdf")
    return FileResponse(path, media_type="application/pdf", filename=filename)


def run_planner(user_query: str) -> Dict[str, Any]:
    load_dotenv()
    graph = build_trip_planner_graph()
    state = initial_state(user_query)
    trace: List[Dict[str, str]] = []

    final_state = state
    for event in graph.stream(state):
        node_name, node_state = next(iter(event.items()))
        final_state = node_state
        trace.append(_trace_event(node_name, node_state))

    pdf_path = Path(final_state.get("pdf_status", {}).get("path", ""))
    pdf_filename = pdf_path.name if pdf_path.name else ""

    return {
        "query": user_query,
        "trace": trace,
        "state": final_state,
        "pdf_filename": pdf_filename,
    }


def _trace_event(node_name: str, state: Dict[str, Any]) -> Dict[str, str]:
    labels = {
        "orchestrator_start": "Orchestrator Agent",
        "user_input": "User Input Agent",
        "memory_retrieval": "Memory Agent",
        "weather": "Weather Agent",
        "transport": "Transport Agent",
        "hotel": "Hotel Agent",
        "places": "Places Explorer Agent",
        "budget": "Budget Agent",
        "itinerary": "Itinerary Agent",
        "final_review": "Final Review Agent",
        "orchestrator_validation": "Orchestrator Agent",
        "memory_update": "Memory Agent",
        "pdf_generator": "PDF Generator Agent",
        "final_response": "Orchestrator Agent",
    }
    label = labels.get(node_name, node_name.replace("_", " ").title())

    if node_name == "orchestrator_start":
        detail = "Understood goal, planned required agents, and started execution."
        status = "Planning"
    elif node_name == "user_input":
        detail = f"Extracted preferences: {state['trip_preferences']}"
        status = "Collected"
    elif node_name == "memory_retrieval":
        detail = f"Retrieved preferences: {state['memory'].get('retrieved_preferences') or 'none'}"
        status = "Memory"
    elif node_name == "weather":
        detail = f"{state['weather_data'].get('source')}: {state['weather_data'].get('risk')} weather risk"
        status = "API"
    elif node_name == "transport":
        selected = state["transport_data"]["recommended"]
        detail = f"{selected['mode']} selected: {selected['summary']}"
        status = "Selected"
    elif node_name == "hotel":
        hotel = state["hotel_data"]["selected"]
        detail = f"{hotel['name']} selected from {hotel.get('source', 'unknown')}"
        status = "Selected"
    elif node_name == "places":
        places = state["places_data"]
        detail = f"{places.get('source', 'unknown')}: {', '.join(places.get('attractions', [])[:3])}"
        status = "Explored"
    elif node_name == "budget":
        budget = state["budget_summary"]
        detail = f"Estimated Rs. {budget['estimated_total']} vs budget Rs. {budget['user_budget']} ({budget['status']})"
        status = "Calculated"
    elif node_name == "itinerary":
        detail = f"Created {len(state['itinerary'].get('days', []))} day-wise itinerary items."
        status = "Built"
    elif node_name == "final_review":
        review = state["review_status"]
        detail = f"Completeness score {review['completeness_score']}; issues: {review['issues'] or 'none'}"
        status = "Reviewed"
    elif node_name == "orchestrator_validation":
        decision = state["orchestrator_decision"]
        detail = f"Approved={decision.get('approved')} retries={decision.get('retries')}"
        status = "Validated"
    elif node_name == "memory_update":
        detail = f"Updated memory store: {state['memory'].get('memory_file')}"
        status = "Saved"
    elif node_name == "pdf_generator":
        detail = f"Generated report: {state['pdf_status'].get('path')}"
        status = "PDF"
    elif node_name == "final_response":
        detail = "Final trip plan is ready."
        status = "Done"
    else:
        detail = "Completed."
        status = "Done"

    return {"agent": label, "status": status, "detail": detail}
