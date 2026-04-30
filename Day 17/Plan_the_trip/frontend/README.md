# AI Trip Planner Frontend

Static frontend for the FastAPI + LangGraph backend.

## Run

Start the backend first:

```powershell
cd "Day 17\Plan_the_trip\backend"
python -m uvicorn app.main:app --reload
```

Start the frontend:

```powershell
cd "Day 17\Plan_the_trip\frontend"
python -m http.server 5173
```

Open:

```text
http://127.0.0.1:5173
```
