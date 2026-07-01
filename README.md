<div align="center">

# ⚡ Clutch

### Your AI deadline agent — comes through when it matters.

Turn a messy brain-dump into a prioritized, time-blocked day — automatically.

**Live app:** _<paste your Cloud Run URL here after deploying>_

`React` · `FastAPI` · `LangGraph` · `Groq / Gemini` · `Google Cloud Run`

</div>

---

## The problem

Students and professionals don't miss deadlines because they lack reminders — they miss them because **reminders are passive**. A notification tells you *that* something is due; it doesn't help you decide what to do first, how long it'll take, or when to fit it in. The result is the classic last-minute scramble.

## The solution

**Clutch** is an AI agent that does the planning *for* you. You describe everything on your plate in plain language; Clutch reads it, prioritizes it, schedules it around your real day, and explains every decision — so you act instead of panic.

---

## What the agent understands (just type naturally)

The agent reads cues straight from your sentence — no forms, no fields:

| You write | Clutch understands |
|---|---|
| "submit report **by Friday**", "rent **today**" | **Deadlines** → urgency |
| "gym **at 6 PM**", "DSA **9–10**" | **Fixed clock times** → anchored exactly |
| "DSA, **then** lunch, **then** emails" | **Order** → kept in that sequence |
| "coding is **hard for me**", "**quick** call" | **Difficulty** → Easy / Normal / Hard |
| "read for **2 hours**" | **Duration** |
| "interview prep, **high priority**" | **Importance** |

## How Clutch schedules your day

The scheduling follows a clear, predictable set of rules:

1. **Fixed times win.** "at 4 PM" or "9–10" is anchored to that exact slot; everything else flows around it.
2. **Your order is respected.** If you say "X then Y then Z", they're placed in that sequence (as a true forward timeline).
3. **Smart priority fills the rest.** Tasks with no time or order are ranked by `urgency + importance + difficulty`, and hard tasks are placed in your peak-focus hours.
4. **Durations:**
   - If you state a time/range/duration, that's used exactly.
   - Otherwise, defaults by difficulty — **Hard = 1h 30m, Normal = 1h, Easy = 45m**.
5. **No collisions.** Flexible tasks never overlap your fixed events; if something can't fit before a fixed block, it's placed after.

## Key features

- **Natural-language capture** — type the way you think; the agent extracts the details.
- **Autonomous, explainable planning** — every task shows *why* it's ranked where it is.
- **Manual reorder** — ↑ / ↓ arrows on each task; move one and the day re-plans instantly (durations kept, times recomputed).
- **Instant in-browser re-planning** — changing difficulty, importance, or order never waits on the server.
- **Transparent assumptions** — the agent reports every guess it made ("No deadline given for X — treated as flexible").
- **Google Calendar integration:**
  - **"Add all to calendar"** → downloads a standard `.ics` with every task and a **10-minute reminder alarm** (imports into Google / Apple / Outlook, syncs to your phone).
  - **"+ Google Calendar"** on each task → one-click, opens Google Calendar with that event pre-filled (no login/OAuth needed).
- **Gamified progress** — earn points and level up by completing tasks on time.
- **Robust with duplicates** — every task has a stable id, so repeated names ("Break", "Make project") never confuse the ordering.

## Architecture

Clutch is an **agentic pipeline** built with LangGraph. The key design choice: the LLM handles *understanding language*, while the *planning math is deterministic Python* — so results are explainable, consistent, and never hallucinated.

```
                ┌─────────── LLM (understands your words) ───────────┐
   your text →  │  parse  →  enrich                                   │
                └────────────────────┬───────────────────────────────┘
                                     │
                ┌──────── deterministic Python (explainable) ─────────┐
                │  prioritize  →  schedule                            │ → plan + .ics
                └─────────────────────────────────────────────────────┘
```

- **parse** — extracts tasks: title, deadline, fixed time, order, duration, importance, difficulty.
- **enrich** — fills only what you didn't specify (category, difficulty); never overrides your input.
- **prioritize** — `score = urgency×2 + importance×1.5 + difficulty`.
- **schedule** — anchors fixed times, honors your order, then smart-fills the rest.

The full priority/schedule logic is **mirrored in the browser** (`frontend/src/planner.js`), so edits and reorders re-plan instantly with zero server calls.

## Tech stack

- **Frontend:** React + Vite
- **Backend:** FastAPI + LangGraph
- **LLM:** provider-switchable via one env var — Groq (`qwen/qwen3-32b`) or Google Gemini (`gemini-2.0-flash`)
- **Deployment:** Google Cloud Run, built by Google Cloud Build — a single container serves both the API and the React app

## Run locally

```bash
# 1. Backend
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # set LLM_PROVIDER and your key
python -m uvicorn app.main:app --reload --port 8001

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev                     # → http://localhost:5173
```

`.env` essentials:

```
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...            # free key at console.groq.com/keys
GROQ_MODEL=qwen/qwen3-32b
```

## Deploy to Google Cloud Run

A single container builds the frontend and serves it from FastAPI alongside the API.

```bash
gcloud run deploy clutch \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars LLM_PROVIDER=groq,GROQ_MODEL=qwen/qwen3-32b,GROQ_API_KEY=YOUR_KEY
```

The command returns a public `https://...run.app` URL — that's the live app.

## Project structure

```
clutch/
├── backend/
│   └── app/
│       ├── main.py         # FastAPI: /plan, /replan, serves the frontend
│       ├── graph.py        # LangGraph agent (parse → enrich → prioritize → schedule)
│       ├── state.py        # task model + graph state
│       ├── llm.py          # provider-switchable LLM (Groq / Gemini)
│       └── ics_export.py   # calendar (.ics) builder with alarms
├── frontend/
│   └── src/
│       ├── App.jsx         # UI
│       ├── api.js          # backend calls
│       └── planner.js      # client-side re-planning + Google Calendar links
└── Dockerfile             # one image: build React + serve via FastAPI
```

---

<div align="center">
Built for the BlockseBlock Hackathon · Problem Statement 1 — "The Last-Minute Life Saver"
</div>
