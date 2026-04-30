"""Specialized agents for the LangGraph trip planner."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict

try:
    import chromadb
except Exception:  # pragma: no cover - optional runtime dependency
    chromadb = None

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional runtime dependency
    ChatOpenAI = None

from pdf_generator import generate_trip_pdf
from tools import estimate_budget, get_places, get_transport_options, get_weather, recommend_hotels


def orchestrator_start_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    state["orchestrator_decision"] = {
        "goal": "Create a complete personalized trip plan and PDF report.",
        "agent_plan": [
            "User Input",
            "Memory Retrieval",
            "Weather",
            "Transport",
            "Hotel",
            "Places",
            "Budget",
            "Itinerary",
            "Final Review",
            "Memory Update",
            "PDF Generator",
        ],
        "approved": False,
        "retries": 0,
    }
    state["trace"].append("Orchestrator understood the trip planning goal.")
    return state


def user_input_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    query = state["user_query"]
    prefs = _parse_trip_query(query)
    missing = []

    defaults = {
        "source": "Bangalore",
        "destination": "Goa",
        "days": 5,
        "budget": 30000,
        "travelers": 2,
        "travel_type": "couple",
        "hotel_preference": "beach resort",
        "food_preference": "seafood",
        "transport_preference": "flight",
        "interests": ["beaches", "nightlife", "sightseeing"],
        "style": "balanced",
    }
    for key, value in defaults.items():
        if key not in prefs or prefs[key] is None or prefs[key] == "" or prefs[key] == []:
            prefs[key] = value
            missing.append(key)

    state["trip_preferences"] = prefs
    state["user_profile"] = {"traveler_type": prefs["travel_type"], "travelers": prefs["travelers"]}
    state["orchestrator_decision"]["missing_info"] = missing
    state["trace"].append("User Input Agent extracted trip preferences.")
    return state


def memory_retrieval_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    memory_file = Path(__file__).parent / "data" / "trip_memory.json"
    memory_file.parent.mkdir(exist_ok=True)
    if memory_file.exists():
        data = json.loads(memory_file.read_text(encoding="utf-8"))
    else:
        data = {}

    destination = state["trip_preferences"]["destination"].lower()
    chroma_results = _retrieve_chroma_memory(destination)
    state["memory"] = {
        "source": "ChromaDB + JSON backup" if chroma_results else "JSON backup",
        "memory_file": str(memory_file),
        "retrieved_preferences": chroma_results or data.get(destination, {}),
        "all_memory": data,
    }
    state["trace"].append("Memory Agent retrieved prior destination preferences.")
    return state


def weather_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    prefs = state["trip_preferences"]
    state["weather_data"] = get_weather(prefs["destination"], prefs["days"])
    state["trace"].append("Weather Agent fetched weather forecast.")
    return state


def transport_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    prefs = state["trip_preferences"]
    preference = prefs["transport_preference"]
    if state["orchestrator_decision"].get("retry_transport"):
        preference = "train"
        prefs["transport_preference"] = "train"
    state["transport_data"] = get_transport_options(
        prefs["source"],
        prefs["destination"],
        preference,
        prefs["travelers"],
    )
    state["trace"].append("Transport Agent selected route options.")
    return state


def hotel_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    prefs = state["trip_preferences"]
    retry_count = state["orchestrator_decision"].get("retries", 0)
    state["hotel_data"] = recommend_hotels(
        prefs["destination"],
        prefs["hotel_preference"],
        prefs["budget"],
        prefs["days"],
        prefs["travelers"],
        retry_count=retry_count,
    )
    state["trace"].append("Hotel Agent recommended hotels.")
    return state


def places_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    prefs = state["trip_preferences"]
    rainy = state["weather_data"].get("risk") == "heavy_rain"
    state["places_data"] = get_places(prefs["destination"], prefs["interests"], rainy=rainy)
    state["trace"].append("Places Explorer Agent selected attractions and local experiences.")
    return state


def budget_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    prefs = state["trip_preferences"]
    state["budget_summary"] = estimate_budget(
        prefs["budget"],
        prefs["days"],
        prefs["travelers"],
        state["transport_data"],
        state["hotel_data"],
        state["places_data"],
    )
    state["trace"].append("Budget Agent estimated and optimized costs.")
    return state


def itinerary_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    prefs = state["trip_preferences"]
    attractions = state["places_data"]["attractions"]
    food = state["places_data"]["food"]
    llm_itinerary = _generate_llm_itinerary(state)
    if llm_itinerary:
        state["itinerary"] = llm_itinerary
        state["trace"].append("Itinerary Agent generated day-wise plan with LLM.")
        return state

    days = []
    for day in range(1, prefs["days"] + 1):
        attraction = attractions[(day - 1) % len(attractions)]
        meal = food[(day - 1) % len(food)]
        days.append(
            {
                "day": day,
                "morning": f"Breakfast and visit {attraction}",
                "afternoon": "Relaxed sightseeing / beach time / cafe break",
                "evening": f"Local dinner: {meal}",
                "tip": "Keep buffer time for transfers and weather changes.",
            }
        )

    state["itinerary"] = {
        "source": "Python fallback",
        "title": f"{prefs['days']}-Day {prefs['destination']} Trip from {prefs['source']}",
        "days": days,
        "packing_checklist": [
            "Government ID",
            "Comfortable footwear",
            "Power bank",
            "Weather-appropriate clothing",
            "Basic medicines",
        ],
        "emergency_contacts": ["Local emergency: 112", "Hotel front desk", "Nearest hospital"],
    }
    state["trace"].append("Itinerary Agent generated day-wise plan.")
    return state


def final_review_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    budget = state["budget_summary"]
    issues = []
    if budget["estimated_total"] > budget["user_budget"]:
        issues.append("Estimated cost exceeds user budget.")
    if not state["itinerary"].get("days"):
        issues.append("Itinerary is missing day-wise plan.")
    if state["weather_data"].get("risk") == "heavy_rain":
        issues.append("Heavy rain risk found; indoor backups included.")

    llm_review = _generate_llm_review(state, issues)
    state["review_status"] = llm_review or {
        "source": "Python rules",
        "valid": not any(issue == "Itinerary is missing day-wise plan." for issue in issues),
        "issues": issues,
        "completeness_score": 95 if not issues else 85,
    }
    state["trace"].append("Final Review Agent checked completeness and conflicts.")
    return state


def orchestrator_validation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    over_budget = state["budget_summary"]["estimated_total"] > state["budget_summary"]["user_budget"]
    retries = state["orchestrator_decision"].get("retries", 0)
    hotel_is_optimized = state["hotel_data"]["selected"]["category"] == "budget optimized"
    transport_is_optimized = state["transport_data"]["recommended"]["mode"] == "train"

    state["orchestrator_decision"]["retry_hotel"] = False
    state["orchestrator_decision"]["retry_transport"] = False

    if over_budget and not hotel_is_optimized:
        state["orchestrator_decision"]["retry_hotel"] = True
        state["orchestrator_decision"]["retries"] = retries + 1
        state["trace"].append("Orchestrator found budget conflict and requested Hotel Agent retry.")
    elif over_budget and not transport_is_optimized:
        state["orchestrator_decision"]["retry_transport"] = True
        state["orchestrator_decision"]["retries"] = retries + 1
        state["trace"].append("Orchestrator found budget conflict and requested Transport Agent retry.")
    else:
        state["orchestrator_decision"]["approved"] = state["review_status"]["valid"]
        state["trace"].append("Orchestrator approved final plan and triggered PDF generation.")
    return state


def memory_update_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    memory_file = Path(state["memory"]["memory_file"])
    data = state["memory"].get("all_memory", {})
    destination = state["trip_preferences"]["destination"].lower()
    data[destination] = {
        "last_hotel_preference": state["trip_preferences"]["hotel_preference"],
        "last_food_preference": state["trip_preferences"]["food_preference"],
        "last_transport_preference": state["trip_preferences"]["transport_preference"],
        "last_budget": state["trip_preferences"]["budget"],
    }
    memory_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    _update_chroma_memory(destination, data[destination])
    state["memory"]["updated"] = True
    state["trace"].append("Memory Agent updated destination preferences.")
    return state


def pdf_generator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    path = generate_trip_pdf(state)
    state["pdf_status"] = {"generated": True, "path": str(path)}
    state["trace"].append("PDF Generator Agent created downloadable trip report.")
    return state


def final_response_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    prefs = state["trip_preferences"]
    budget = state["budget_summary"]
    state["final_answer"] = (
        f"Your {prefs['days']}-day {prefs['destination']} trip from {prefs['source']} is ready.\n"
        f"Travel style: {prefs['travel_type']} | Travelers: {prefs['travelers']} | Preference: {prefs['style']}\n"
        f"Weather source: {state['weather_data'].get('source', 'unknown')}\n"
        f"Transport: {state['transport_data']['recommended']['mode']} - {state['transport_data']['recommended']['summary']}\n"
        f"Hotel: {state['hotel_data']['selected']['name']} at approx Rs. {state['hotel_data']['selected']['total_cost']} "
        f"({state['hotel_data']['selected'].get('source', 'unknown')})\n"
        f"Places source: {state['places_data'].get('source', 'unknown')}\n"
        f"Estimated total: Rs. {budget['estimated_total']} against budget Rs. {budget['user_budget']} "
        f"({budget['status']}).\n"
        f"PDF generated at: {state['pdf_status']['path']}"
    )
    state["trace"].append("Orchestrator returned final answer.")
    return state


def _parse_trip_query(query: str) -> Dict[str, Any]:
    text = query.lower()
    prefs: Dict[str, Any] = {}

    days = re.search(r"(\d+)\s*[- ]?day", text)
    if days:
        prefs["days"] = int(days.group(1))

    budget = re.search(r"(?:budget|rs\.?|inr|₹)\s*[:\-]?\s*([0-9,]+)", text)
    if budget:
        prefs["budget"] = int(budget.group(1).replace(",", ""))

    travelers = re.search(r"for\s+(?:a\s+)?(\d+)\s+(?:people|travelers|persons)", text)
    if travelers:
        prefs["travelers"] = int(travelers.group(1))
    elif "couple" in text:
        prefs["travelers"] = 2
        prefs["travel_type"] = "couple"
    elif "family" in text:
        prefs["travel_type"] = "family"
    elif "solo" in text:
        prefs["travelers"] = 1
        prefs["travel_type"] = "solo"
    elif "business" in text:
        prefs["travel_type"] = "business"

    route = re.search(r"(?:from)\s+([a-zA-Z ]+?)\s+(?:to|for)\s+([a-zA-Z ]+?)(?:\s+for|\s+with|\s+budget|$)", query, re.I)
    if route:
        prefs["source"] = route.group(1).strip().title()
        prefs["destination"] = route.group(2).strip().title()
    else:
        trip_from = re.search(r"([a-zA-Z]+)\s+trip\s+from\s+([a-zA-Z ]+?)(?:\s+for|\s+with|\.|,|$)", query, re.I)
        if trip_from:
            prefs["destination"] = trip_from.group(1).strip().title()
            prefs["source"] = trip_from.group(2).strip().title()
        else:
            destination = re.search(r"\b(?:to|in)\s+([a-zA-Z]+)", query, re.I)
            if destination:
                prefs["destination"] = destination.group(1).strip().title()

    if "flight" in text:
        prefs["transport_preference"] = "flight"
    elif "train" in text:
        prefs["transport_preference"] = "train"
    elif "car" in text or "road" in text:
        prefs["transport_preference"] = "car"

    if "beach resort" in text:
        prefs["hotel_preference"] = "beach resort"
    elif "hotel" in text:
        prefs["hotel_preference"] = "hotel"
    elif "hostel" in text:
        prefs["hotel_preference"] = "hostel"

    if "seafood" in text:
        prefs["food_preference"] = "seafood"
    elif "vegetarian" in text or "veg" in text:
        prefs["food_preference"] = "vegetarian"

    interests = []
    for word in ["beaches", "nightlife", "sightseeing", "shopping", "temples", "museums", "adventure"]:
        if word in text:
            interests.append(word)
    if interests:
        prefs["interests"] = interests

    if "luxury" in text:
        prefs["style"] = "luxury"
    elif "budget" in text:
        prefs["style"] = "budget"

    return prefs


def _generate_llm_itinerary(state: Dict[str, Any]) -> Dict[str, Any] | None:
    llm = _build_llm()
    if not llm:
        return None
    prefs = state["trip_preferences"]
    prompt = (
        "Create a travel itinerary as strict JSON only. "
        "Keys: title, days, packing_checklist, emergency_contacts. "
        "Each day item must have day, morning, afternoon, evening, tip.\n\n"
        f"Preferences: {json.dumps(prefs)}\n"
        f"Weather: {json.dumps(state['weather_data'])}\n"
        f"Transport: {json.dumps(state['transport_data'])}\n"
        f"Hotel: {json.dumps(state['hotel_data'])}\n"
        f"Places: {json.dumps(state['places_data'])}\n"
    )
    try:
        parsed = json.loads(llm.invoke(prompt).content)
    except Exception:
        return None
    if not isinstance(parsed, dict) or not parsed.get("days"):
        return None
    parsed["source"] = "LLM"
    return parsed


def _generate_llm_review(state: Dict[str, Any], issues: list[str]) -> Dict[str, Any] | None:
    llm = _build_llm()
    if not llm:
        return None
    prompt = (
        "Review this trip plan. Return strict JSON only with keys: "
        "source, valid, issues, completeness_score.\n\n"
        f"Detected rule issues: {issues}\n"
        f"Budget: {json.dumps(state['budget_summary'])}\n"
        f"Itinerary: {json.dumps(state['itinerary'])}\n"
        f"Weather: {json.dumps(state['weather_data'])}\n"
    )
    try:
        parsed = json.loads(llm.invoke(prompt).content)
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    parsed["source"] = "LLM"
    parsed.setdefault("valid", not issues)
    parsed.setdefault("issues", issues)
    parsed.setdefault("completeness_score", 90 if not issues else 80)
    return parsed


def _build_llm():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not ChatOpenAI or not api_key.startswith("sk-"):
        return None
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.2)


def _retrieve_chroma_memory(destination: str) -> Dict[str, Any]:
    collection = _memory_collection()
    if not collection:
        return {}
    try:
        result = collection.query(query_embeddings=[_simple_embedding(destination)], n_results=1)
        documents = result.get("documents", [[]])[0]
        if not documents:
            return {}
        return json.loads(documents[0])
    except Exception:
        return {}


def _update_chroma_memory(destination: str, preferences: Dict[str, Any]) -> None:
    collection = _memory_collection()
    if not collection:
        return
    try:
        collection.upsert(
            ids=[destination],
            documents=[json.dumps(preferences)],
            embeddings=[_simple_embedding(destination)],
            metadatas=[{"destination": destination}],
        )
    except Exception:
        return


def _memory_collection():
    if not chromadb:
        return None
    try:
        path = str(Path(__file__).parent / "chroma_memory")
        client = chromadb.PersistentClient(path=path)
        return client.get_or_create_collection("trip_preferences")
    except Exception:
        return None


def _simple_embedding(text: str) -> list[float]:
    buckets = [0.0] * 16
    for index, char in enumerate(text.lower()):
        buckets[index % len(buckets)] += (ord(char) % 31) / 31
    total = sum(buckets) or 1.0
    return [round(value / total, 6) for value in buckets]
