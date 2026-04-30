# AI Trip Planner Backend

Production-oriented FastAPI + LangGraph backend with a supervisor-style multi-agent workflow.

## Folder Structure

```text
backend/
  app/
    main.py
    config.py
    state_schema.py
    agents/
    orchestrator/
    tools/
    memory/
    graph/
    prompts/
    services/
    utils/
  storage/
    pdfs/
    vector_store/
  requirements.txt
  .env.example
```

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## API

`POST /plan-trip`

```json
{
  "source": "Delhi",
  "destination": "Goa",
  "start_date": "2026-05-10",
  "end_date": "2026-05-14",
  "budget": 60000,
  "travellers": 2,
  "preferences": ["beaches", "food", "relaxed pace"],
  "user_id": "demo-user"
}
```

The app calls real APIs when keys are configured. Weather uses OpenWeatherMap, transport uses Aviationstack flights, and both hotels and places use Geoapify Places. If a key is missing or a provider fails, the relevant agent returns a transparent fallback result so local development still produces a complete trip plan and PDF.

## LangSmith Tracing

Enable LangSmith by adding these values to `.env`:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=ai-trip-planner
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

Run the backend normally:

```bash
uvicorn app.main:app --reload
```

Trip requests are traced as `plan_trip_request`, the LangGraph run is tagged as `ai_trip_planner_graph`, and each agent appears as its own LangSmith span.
