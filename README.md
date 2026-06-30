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

```
You type:  "DSA assignment by Friday, it's hard for me and high priority.
            Pay rent today, quick. Prep ~2 hours for the interview tomorrow."

Clutch returns:  a ranked task list + an hour-by-hour schedule that puts the
                 hard task in your peak-focus window, fits the quick one into a
                 gap, respects your classes and sleep — plus a calendar file
                 with reminders.
```

---

## Key features

| | Feature | What it does |
|---|---|---|
| 🧠 | **Natural-language capture** | No forms. It reads cues like *"hard for me"*, *"urgent"*, *"today"*, *"2 hours"* straight from your sentence. |
| 🎯 | **Autonomous prioritization** | Scores every task from deadline urgency + importance + difficulty, and ranks them. |
| 🗓️ | **Energy-aware scheduling** | Places hard tasks in your peak-focus hours and works around sleep and fixed commitments. |
| 💬 | **Transparent reasoning** | Shows *why* each task ranks where it does, and every assumption it made. |
| ⚡ | **Instant re-planning** | Change a task's difficulty or importance and the whole day re-plans in the browser — no waiting. |
| 📅 | **Calendar export with alarms** | One click downloads an `.ics` with reminders, for Google / Apple / Outlook calendars. |
| 🏆 | **Gamified progress** | Earn points and level up by finishing tasks on time. |

---

## How it works

Clutch is built as an **agentic pipeline** using LangGraph. The key design choice: the LLM handles *understanding language*, while the *planning math is deterministic Python* — so results are explainable, consistent, and never hallucinated.

```
                ┌─────────── LLM (understands your words) ───────────┐
   your text →  │  parse  →  enrich                                   │
                └────────────────────┬───────────────────────────────┘
                                     │
                ┌──────── deterministic Python (explainable) ─────────┐
                │  prioritize  →  schedule                            │ → plan + .ics
                └─────────────────────────────────────────────────────┘
```

- **parse** — extracts tasks: title, deadline, duration, importance, difficulty.
- **enrich** — fills only what you didn't specify (category, difficulty); never overrides your own input.
- **prioritize** — `score = urgency×2 + importance×1.5 + difficulty` (fully explainable).
- **schedule** — greedy time-blocking around fixed blocks and sleep, hard tasks first into peak hours.

The same priority/schedule logic is **mirrored in the browser** (`frontend/src/planner.js`), so editing a task re-plans instantly with zero server calls.

---

## Tech stack

- **Frontend:** React + Vite
- **Backend:** FastAPI + LangGraph
- **LLM:** provider-switchable via one env var — Groq (`qwen/qwen3-32b`) or Google Gemini (`gemini-2.0-flash`)
- **Deployment:** Google Cloud Run, built by Google Cloud Build — a single container serves both the API and the React app

---

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

---

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

---

## Project structure

```
clutch/
├── backend/
│   └── app/
│       ├── main.py         # FastAPI: /plan, /replan, serves the frontend
│       ├── graph.py        # LangGraph agent (parse → enrich → prioritize → schedule)
│       ├── state.py        # task model + graph state
│       ├── llm.py          # provider-switchable LLM (Groq / Gemini)
│       └── ics_export.py   # calendar file builder
├── frontend/
│   └── src/
│       ├── App.jsx         # UI
│       ├── api.js          # backend calls
│       └── planner.js      # client-side re-planning (mirrors backend math)
└── Dockerfile             # one image: build React + serve via FastAPI
```

---

<div align="center">
Built for the BlockseBlock Hackathon · Problem Statement 1 — "The Last-Minute Life Saver"
</div>
