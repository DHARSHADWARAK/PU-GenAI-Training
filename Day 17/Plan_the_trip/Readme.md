# Plan the Trip - AI Trip Planner

Plan the Trip is a full-stack AI travel planning project built with a FastAPI backend, a LangGraph multi-agent workflow, and a static HTML/CSS/JavaScript frontend. It collects trip preferences, coordinates specialized agents, generates a day-wise itinerary, checks budget fit, and produces a downloadable PDF trip report.

## Project Highlights

- Multi-agent trip planning workflow using LangGraph.
- FastAPI backend with `/health` and `/plan-trip` endpoints.
- Static frontend for submitting trip details and viewing generated results.
- Agents for input validation, memory, weather, transport, hotels, places, budget, itinerary, final review, and PDF generation.
- Optional real API integrations for weather, flights, hotels, and places.
- Fallback responses when external API keys are missing, so the app can still run locally.
- PDF report generation through ReportLab.
- Optional LangSmith tracing for observing the graph and agent runs.

## Folder Structure

```text
Plan_the_trip/
  backend/
    app/
      agents/           # Specialized trip planning agents
      graph/            # LangGraph workflow
      memory/           # Session and vector memory helpers
      observability/    # LangSmith tracing setup
      orchestrator/     # Supervisor/orchestration logic
      prompts/          # Itinerary prompt templates
      services/         # Trip, LLM, and PDF services
      tools/            # Weather, hotel, places, transport API clients
      utils/            # Logging and date helpers
      main.py           # FastAPI application
      config.py         # Environment-based settings
      state_schema.py   # Shared graph state
    storage/
      pdfs/             # Generated PDF reports
      vector_store/     # Local vector memory files
    requirements.txt
    .env.example
  frontend/
    index.html
    app.js
    styles.css
    README.md
  Readme.md
```

## Tech Stack

- Python
- FastAPI
- LangGraph
- LangChain Core
- OpenAI-compatible LLM configuration
- LangSmith tracing
- ReportLab
- FAISS
- HTML, CSS, and JavaScript

## Agent Workflow

The backend starts from the submitted trip payload and builds a shared state for the LangGraph workflow.

The main agents are:

- User Input Agent: normalizes user profile and trip preferences.
- Memory Agent: stores or retrieves useful context for the user.
- Weather Agent: gets destination weather or returns a fallback summary.
- Transport Agent: estimates travel options and cost.
- Hotel Agent: recommends accommodation.
- Places Agent: finds attractions and activities.
- Budget Agent: compares estimated costs against the requested budget.
- Itinerary Agent: creates the day-wise plan.
- Final Review Agent: checks the plan for missing or inconsistent details.
- PDF Generator Agent: creates a PDF report and returns its link.

## Backend Setup

Open a terminal from the project root:

```powershell
cd "Day 17\Plan_the_trip\backend"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:

```powershell
copy .env.example .env
```

Add any keys you want to use:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
OPENWEATHER_API_KEY=your_openweather_key
AVIATIONSTACK_API_KEY=your_aviationstack_key
GEOAPIFY_API_KEY=your_geoapify_key
APP_BASE_URL=http://localhost:8000
```

External API keys are optional for local demos. If a provider key is not configured, the related agent returns a transparent fallback result.

## Run the Backend

```powershell
cd "Day 17\Plan_the_trip\backend"
.\.venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Run the Frontend

Start a second terminal:

```powershell
cd "Day 17\Plan_the_trip\frontend"
python -m http.server 5173
```

Open:

```text
http://127.0.0.1:5173
```

The frontend sends requests to:

```text
http://127.0.0.1:8000/plan-trip
```

## API Usage

Endpoint:

```text
POST /plan-trip
```

Sample request:

```json
{
  "source": "Delhi",
  "destination": "Goa",
  "start_date": "2026-05-10",
  "end_date": "2026-05-14",
  "budget": 60000,
  "currency": "INR",
  "travellers": 2,
  "preferences": ["beaches", "food", "relaxed pace"],
  "pace": "balanced",
  "user_id": "demo-user"
}
```

Sample response fields:

```text
user_profile
trip_preferences
weather_data
hotel_data
transport_data
places_data
budget_summary
itinerary
review_status
pdf_status
orchestrator_decision
pdf_link
```

Generated PDFs are served from:

```text
http://localhost:8000/pdfs/
```

## LangSmith Tracing

To enable LangSmith tracing, add these values to `backend/.env`:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=ai-trip-planner
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

When tracing is enabled, trip requests are traced as `plan_trip_request`, and the LangGraph run is tagged as `ai_trip_planner_graph`.

## Notes

- Keep real API keys only in `.env`; do not commit them.
- Generated PDF files and vector-store data are local runtime artifacts.
- The root `.gitignore` is configured to ignore local storage, vector stores, environments, and secret files.
- If the frontend shows `API offline`, make sure the backend is running on port `8000`.
