"""Streamlit frontend for the Multi-Agent Trip Planner.

Run:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv

from workflow import build_trip_planner_graph, initial_state


SAMPLE_QUERY = (
    "Plan a 5-day Goa trip from Bangalore for a couple. Budget: 30000. "
    "Need beach resort, nightlife, sightseeing, seafood, flight preferred."
)


AGENT_LABELS = {
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


def main() -> None:
    load_dotenv(override=True)
    st.set_page_config(page_title="Multi-Agent Trip Planner", page_icon="✈️", layout="wide")
    _inject_css()

    st.title("Multi-Agent Trip Planner")
    st.caption("LangGraph orchestration with memory, real API tools, budget retries, itinerary planning, and PDF generation.")

    with st.sidebar:
        st.subheader("Trip Request")
        trip_request = st.text_area("Describe your trip", value=SAMPLE_QUERY, height=230)
        run_clicked = st.button("Generate Trip Plan", type="primary", use_container_width=True)
        clear_clicked = st.button("Clear Previous Result", use_container_width=True)

        st.divider()
        st.subheader("Agent Stack")
        for agent in [
            "Orchestrator",
            "User Input",
            "Memory",
            "Weather",
            "Transport",
            "Hotel",
            "Places",
            "Budget",
            "Itinerary",
            "Final Review",
            "PDF Generator",
        ]:
            st.markdown(f"- {agent}")

        st.divider()
        st.subheader("API Status")
        st.write("Transport / ORS:", "Configured" if _has_env("OPENROUTESERVICE_API_KEY") else "Missing")
        st.write("Weather / OpenWeather:", "Configured" if _has_env("OPENWEATHER_API_KEY") else "Missing")
        st.write("Hotels / MakCorps:", "Configured" if _has_env("MAKCORPS_API_KEY") else "Missing")
        st.write("Places / Geoapify:", "Configured" if _has_env("GEOAPIFY_API_KEY") else "Missing")
        st.write("LLM / OpenAI:", "Configured" if _has_env("OPENAI_API_KEY") else "Missing")

    if "planner_result" not in st.session_state:
        st.session_state.planner_result = None

    if clear_clicked:
        st.session_state.planner_result = None
        st.rerun()

    if run_clicked:
        st.session_state.planner_result = run_planner_with_live_trace(trip_request)

    if st.session_state.planner_result:
        render_result(st.session_state.planner_result)
    else:
        render_empty_state()


def run_planner_with_live_trace(user_query: str) -> Dict[str, Any]:
    load_dotenv(override=True)
    graph = build_trip_planner_graph()
    state = initial_state(user_query)
    trace: List[Dict[str, str]] = []

    progress = st.progress(0)
    trace_area = st.container()
    final_state = state

    node_count_estimate = 14
    for index, event in enumerate(graph.stream(state), start=1):
        node_name, node_state = next(iter(event.items()))
        final_state = node_state
        trace_item = build_trace_item(node_name, node_state)
        trace.append(trace_item)
        progress.progress(min(index / node_count_estimate, 1.0))

        with trace_area:
            st.info(f"{trace_item['agent']} - {trace_item['status']}: {trace_item['detail']}")

    progress.progress(1.0)
    return {"query": user_query, "trace": trace, "state": final_state}


def render_empty_state() -> None:
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown(
            """
            <div class="hero-panel">
              <h2>Plan a full trip in one workflow</h2>
              <p>Enter a travel request and the orchestrator will run specialized agents for requirements, memory, weather, transport, hotels, places, budget, itinerary, review, and PDF generation.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown("#### Expected Output")
        st.write("Complete trip plan")
        st.write("Day-wise itinerary")
        st.write("Budget optimization")
        st.write("Weather and places sources")
        st.write("Downloadable PDF")


def render_result(result: Dict[str, Any]) -> None:
    state = result["state"]
    prefs = state["trip_preferences"]
    budget = state["budget_summary"]
    hotel = state["hotel_data"]["selected"]
    transport = state["transport_data"]["recommended"]
    weather = state["weather_data"]
    places = state["places_data"]

    st.subheader(f"{prefs['days']}-Day {prefs['destination']} Trip from {prefs['source']}")
    st.write(state["final_answer"])

    metric_cols = st.columns(5)
    metric_cols[0].metric("Budget", f"Rs. {budget['user_budget']}")
    metric_cols[1].metric("Estimated", f"Rs. {budget['estimated_total']}")
    metric_cols[2].metric("Status", budget["status"].title())
    metric_cols[3].metric("Travelers", prefs["travelers"])
    metric_cols[4].metric("Retries", state["orchestrator_decision"].get("retries", 0))

    pdf_path = Path(state.get("pdf_status", {}).get("path", ""))
    if pdf_path.exists():
        st.download_button(
            "Download PDF Report",
            data=pdf_path.read_bytes(),
            file_name=pdf_path.name,
            mime="application/pdf",
            type="primary",
        )

    tab_overview, tab_agents, tab_itinerary, tab_budget, tab_raw = st.tabs(
        ["Overview", "Agent Flow", "Itinerary", "Budget", "Raw State"]
    )

    with tab_overview:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Transport")
            st.write(f"Mode: **{transport['mode']}**")
            st.write(f"Source: **{state['transport_data'].get('source', 'unknown')}**")
            st.write(transport["summary"])
            st.write(f"Estimated cost: Rs. {transport['cost']}")

            st.markdown("### Weather")
            st.write(f"Source: **{weather.get('source', 'unknown')}**")
            st.write(f"Risk: **{weather.get('risk', 'unknown')}**")
            for day in weather.get("forecast", [])[:5]:
                temp = f", {day.get('temperature_c')} C" if day.get("temperature_c") is not None else ""
                st.write(f"Day {day.get('day')}: {day.get('condition')}{temp}")

        with col2:
            st.markdown("### Hotel")
            st.write(f"Name: **{hotel['name']}**")
            st.write(f"Category: {hotel['category']}")
            st.write(f"Source: {hotel.get('source', 'unknown')}")
            st.write(f"Total: Rs. {hotel['total_cost']}")

            st.markdown("### Places")
            st.write(f"Source: **{places.get('source', 'unknown')}**")
            for place in places.get("attractions", []):
                st.write(f"- {place}")

    with tab_agents:
        for index, item in enumerate(result["trace"], start=1):
            with st.expander(f"{index}. {item['agent']} - {item['status']}", expanded=index <= 5):
                st.write(item["detail"])

    with tab_itinerary:
        for day in state["itinerary"].get("days", []):
            with st.container(border=True):
                st.markdown(f"#### Day {day['day']}")
                st.write(f"**Morning:** {day['morning']}")
                st.write(f"**Afternoon:** {day['afternoon']}")
                st.write(f"**Evening:** {day['evening']}")
                st.caption(day["tip"])

    with tab_budget:
        st.markdown("### Cost Breakdown")
        cost_rows = {
            "Transport": budget["transport"],
            "Hotel": budget["hotel"],
            "Food": budget["food"],
            "Local Transfers": budget["local_transfers"],
            "Activities": budget["activities"],
            "Buffer": budget["buffer"],
            "Estimated Total": budget["estimated_total"],
        }
        st.bar_chart(cost_rows)
        st.write(budget["optimization_tip"])

    with tab_raw:
        st.json(state)


def build_trace_item(node_name: str, state: Dict[str, Any]) -> Dict[str, str]:
    label = AGENT_LABELS.get(node_name, node_name.replace("_", " ").title())

    if node_name == "orchestrator_start":
        return {"agent": label, "status": "Planning", "detail": "Understood goal and planned the agent execution order."}
    if node_name == "user_input":
        return {"agent": label, "status": "Collected", "detail": str(state["trip_preferences"])}
    if node_name == "memory_retrieval":
        return {"agent": label, "status": "Memory", "detail": str(state["memory"].get("retrieved_preferences") or "No prior preferences")}
    if node_name == "weather":
        return {"agent": label, "status": "API", "detail": f"{state['weather_data'].get('source')}: {state['weather_data'].get('risk')} risk"}
    if node_name == "transport":
        selected = state["transport_data"]["recommended"]
        return {"agent": label, "status": "Selected", "detail": f"{selected['mode']} - {selected['summary']}"}
    if node_name == "hotel":
        hotel = state["hotel_data"]["selected"]
        return {"agent": label, "status": "Selected", "detail": f"{hotel['name']} from {hotel.get('source', 'unknown')}"}
    if node_name == "places":
        places = state["places_data"]
        return {"agent": label, "status": "Explored", "detail": f"{places.get('source')}: {', '.join(places.get('attractions', [])[:4])}"}
    if node_name == "budget":
        budget = state["budget_summary"]
        return {"agent": label, "status": "Calculated", "detail": f"Rs. {budget['estimated_total']} vs Rs. {budget['user_budget']} ({budget['status']})"}
    if node_name == "itinerary":
        return {"agent": label, "status": "Built", "detail": f"{len(state['itinerary'].get('days', []))} itinerary days created."}
    if node_name == "final_review":
        review = state["review_status"]
        return {"agent": label, "status": "Reviewed", "detail": f"Score {review['completeness_score']}; issues: {review['issues'] or 'none'}"}
    if node_name == "orchestrator_validation":
        decision = state["orchestrator_decision"]
        return {"agent": label, "status": "Validated", "detail": f"Approved={decision.get('approved')} retries={decision.get('retries')}"}
    if node_name == "memory_update":
        return {"agent": label, "status": "Saved", "detail": f"Memory updated at {state['memory'].get('memory_file')}"}
    if node_name == "pdf_generator":
        return {"agent": label, "status": "PDF", "detail": f"Generated {state['pdf_status'].get('path')}"}
    if node_name == "final_response":
        return {"agent": label, "status": "Done", "detail": "Final response ready."}
    return {"agent": label, "status": "Done", "detail": "Completed."}


def _has_env(name: str) -> bool:
    import os

    return bool(os.getenv(name, "").strip())


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1280px; }
        [data-testid="stSidebar"] { background: #f6f8fb; border-right: 1px solid #dde4ef; }
        .hero-panel {
            border: 1px solid #dde4ef;
            background: #ffffff;
            border-radius: 8px;
            padding: 32px;
            box-shadow: 0 16px 36px rgba(27, 42, 70, 0.10);
        }
        .hero-panel h2 { margin: 0 0 10px 0; font-size: 30px; }
        .hero-panel p { color: #5d6b82; font-size: 17px; line-height: 1.55; }
        div[data-testid="stMetric"] {
            border: 1px solid #dde4ef;
            background: #ffffff;
            border-radius: 8px;
            padding: 14px;
        }
        button[kind="primary"] { border-radius: 8px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
