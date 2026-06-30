# Clutch

An AI productivity companion that turns a plain-language brain-dump into a prioritized, time-blocked day — and proactively explains its reasoning. Built for BlockseBlock Hackathon, Problem Statement 1 ("The Last-Minute Life Saver").

**Live app:** _<paste your Cloud Run URL here after deploying>_

## What it does

1. **Understands you in plain language.** Type tasks however you think them — "DSA assignment by Friday, it's hard for me; pay rent today, quick." The agent extracts deadlines, durations, importance, and difficulty from your words.
2. **Plans autonomously.** It categorizes, scores priority (urgency + importance + difficulty), and lays out a schedule around your sleep, fixed commitments, and peak-focus hours — putting hard tasks in your sharpest window.
3. **Is transparent.** It surfaces every assumption it made ("No deadline given for X — treated as flexible").
4. **Adapts instantly.** Adjust any task's difficulty or importance and the day re-plans in the browser, instantly.
5. **Exports to your calendar.** One click downloads an `.ics` file with reminders/alarms, importable into Google Calendar, Apple Calendar, or Outlook.
6. **Keeps you moving.** Completing tasks earns points and levels.

## Architecture

```
React (Vite) frontend
        │  POST /plan, /replan
        ▼
FastAPI + LangGraph agent
   parse → enrich → prioritize → schedule
     │       │           └────────── deterministic Python (explainable)
     └───────┴── LLM (understands language)
```

- **parse / enrich** use an LLM to read language and fill gaps.
- **prioritize / schedule** are deterministic Python, so the plan is explainable and reproducible.
- The same priority/schedule math is mirrored in the browser (`planner.js`) for instant re-planning.

## Tech stack

- **Frontend:** React, Vite
- **Backend:** FastAPI, LangGraph
- **LLM:** switchable via `LLM_PROVIDER` — Groq (`qwen/qwen3-32b`) or Google Gemini
- **Deployment:** Google Cloud Run (built with Google Cloud Build), single container serving API + frontend

## Run locally

```bash
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # set LLM_PROVIDER + key
python -m uvicorn app.main:app --reload --port 8001

# Frontend (new terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

## Deploy to Google Cloud Run

```bash
gcloud run deploy clutch \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars LLM_PROVIDER=groq,GROQ_MODEL=qwen/qwen3-32b,GROQ_API_KEY=YOUR_KEY
```

One container builds the React app and serves it from FastAPI alongside the API.
