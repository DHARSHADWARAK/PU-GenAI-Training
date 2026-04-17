# Customer Support AI

AI-assisted customer support response generator built for the Day 11 assignment.

## What it does

- Accepts a customer complaint from a React UI
- Retrieves the top 3 local policy matches using BM25
- Builds one of three prompts:
  - Scenario A: Strict Policy Mode
  - Scenario B: Friendly Tone Mode
  - Scenario C: Fallback Mode
- Calls the Sarvam chat completion API when `SARVAM_API_KEY` is configured
- Logs query, retrieved docs, prompt, and parameters to `logs/app.log`

## Backend setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs on `http://127.0.0.1:8000`.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://127.0.0.1:5173`.

## Environment

Edit the root `.env` file and add your Sarvam key:

```env
SARVAM_API_KEY=your_key_here
```

If the key is missing or the API call fails, the backend returns a safe local fallback response so the UI still works.
