# Multi-Agent Trip Planner using LangGraph

This project implements the Day 17 assignment: a production-style agentic trip planner with memory, an orchestrator agent, specialized agents, and PDF report generation.

## Architecture

```text
START
  |
  v
Orchestrator Agent
  |
User Input Agent
  |
Memory Retrieval Agent
  |
Weather Agent
  |
Transport Agent
  |
Hotel Agent
  |
Places Explorer Agent
  |
Budget Agent
  |
Itinerary Agent
  |
Final Review Agent
  |
Orchestrator Validation
  |-- if conflict --> retry required agent
  |
Memory Update Agent
  |
PDF Generator Agent
  |
FINAL OUTPUT
```

## Agents

| Agent | Responsibility |
|---|---|
| Orchestrator Agent | Controls routing, retries, validation, and PDF trigger |
| User Input Agent | Extracts source, destination, budget, dates/days, travelers, preferences |
| Memory Agent | Retrieves and updates past preferences |
| Weather Agent | Provides forecast and weather risk |
| Transport Agent | Suggests flight/train/car routes |
| Hotel Agent | Finds hotels within preference and budget |
| Places Explorer Agent | Suggests attractions, food, local experiences |
| Budget Agent | Estimates cost and optimization |
| Itinerary Agent | Builds day-wise plan |
| Final Review Agent | Checks completeness and conflicts |
| PDF Generator Agent | Generates final downloadable PDF |

## Run

CLI:

```powershell
cd "c:\Users\Administrator\Downloads\ML\PU-GenAI-Training\Day 17\trip_planner"
python main.py
```

Streamlit frontend:

```powershell
cd "c:\Users\Administrator\Downloads\ML\PU-GenAI-Training\Day 17\trip_planner"
streamlit run streamlit_app.py
```

Then open:

```text
http://localhost:8501
```

FastAPI frontend is also available if needed:

```powershell
uvicorn web_app:app --reload --port 8017
```

Sample query:

```text
Plan a 5-day Goa trip from Bangalore for a couple. Budget: 30000. Need beach resort, nightlife, sightseeing, seafood, flight preferred.
```

## Output

The app prints a step-by-step agent trace and generates a PDF report in:

```text
reports/
```

## Optional APIs

Create `.env` in this folder for live API-backed agents:

```env
OPENWEATHER_API_KEY=your_openweather_key
OPENROUTESERVICE_API_KEY=your_openrouteservice_key
MAKCORPS_API_KEY=your_makcorps_key
GEOAPIFY_API_KEY=your_geoapify_key
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## Agent/API Mapping

| Agent | API / Backend |
|---|---|
| Transport | OpenRouteService Directions API |
| Weather | OpenWeatherMap |
| Hotels | MakCorps |
| Places Explorer | Geoapify Places API |
| Budget | Python calculator |
| Memory | ChromaDB with JSON backup |
| Itinerary | LLM when `OPENAI_API_KEY` is configured |
| Final Review | LLM when `OPENAI_API_KEY` is configured |
| PDF | ReportLab |
| Orchestrator | LangGraph |

If an API key is missing or a call fails, the project keeps a visible local fallback so the graph can still complete.

## State Schema

```python
{
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
}
```

## Notes

- Local fallbacks are kept only so the graph can still run if an API is unavailable.
- Memory is stored in ChromaDB under `chroma_memory/` and mirrored to `data/trip_memory.json`.
- PDF generation uses ReportLab.
