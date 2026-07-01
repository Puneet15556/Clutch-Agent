<div align="center">

# ⚡ Clutch

### Your AI deadline agent — comes through when it matters.

Turn a messy brain-dump into a prioritized, time-blocked day — automatically.

### 🔗 Live app: **https://clutch-agent.onrender.com/**

`React` · `FastAPI` · `LangGraph` · `Groq (qwen3-32b)` · `Docker`

*(Free hosting — the first load after idle may take ~30–50s to wake up.)*

</div>

---

## The problem

People don't miss deadlines because they lack reminders — they miss them because **reminders are passive**. A notification tells you *that* something is due; it doesn't help you decide what to do first, how long it'll take, or when to fit it in. The result is the classic last-minute scramble.

## The solution

**Clutch** is an AI agent that does the planning *for* you. Describe everything on your plate in plain language; Clutch reads it, prioritizes it, schedules it around your real day, and explains every decision — so you take action instead of panicking.

```
You type:  "DSA 9–10, it's hard for me. Then revise ML, then a break.
            Gym at 6 PM. Pay rent today, quick.
            Prep 2 hours for the interview tomorrow — high priority."

Clutch returns:  a ranked task list + an hour-by-hour schedule that anchors
                 your fixed times, keeps your order, sizes each block, and hands
                 you a calendar file with reminders.
```

---

## ✨ Features

- 🧠 **Natural-language capture** — no forms; type the way you think and the agent extracts the details.
- ⏰ **Fixed clock times** — "gym at 6 PM" or "DSA 9–10" is anchored to that exact slot; everything flows around it.
- 🔢 **Respects your order** — "X then Y then Z" is scheduled as a true forward sequence.
- 🎯 **Smart prioritization** — a plain list is ranked by `urgency + importance + difficulty`, with hard tasks placed in your peak-focus hours.
- ⏱️ **Difficulty-based durations** — no time given? Hard = 1h 30m, Normal = 1h, Easy = 45m. Any explicit time/range overrides this.
- ↕️ **Manual reorder** — up/down arrows on each task instantly re-plan the day (durations kept, times recomputed).
- ⚡ **Instant re-planning** — changing difficulty, importance, or order happens in the browser with zero wait.
- 💬 **Transparent reasoning** — every task shows *why* it ranks where it does, plus the assumptions the agent made.
- 📅 **Google Calendar integration** — **"Add all to calendar"** downloads an `.ics` with 10-minute reminder alarms (Google/Apple/Outlook, syncs to your phone); each task also has a one-click **"+ Google Calendar"** quick-add.
- 🏆 **Gamified progress** — earn points and level up by finishing tasks on time.
- 🧩 **Robust with duplicates** — every task has a stable id, so repeated names ("Break", "Make project") never confuse the ordering.

---

## What the agent understands (just type naturally)

| You write | Clutch understands |
|---|---|
| "submit report **by Friday**", "rent **today**" | **Deadlines** → urgency |
| "gym **at 6 PM**", "DSA **9–10**" | **Fixed clock times** → anchored exactly |
| "DSA, **then** lunch, **then** emails" | **Order** → kept in sequence |
| "coding is **hard for me**", "**quick** call" | **Difficulty** → Easy / Normal / Hard |
| "read for **2 hours**" | **Duration** |
| "interview prep, **high priority**" | **Importance** |

## How Clutch schedules your day

1. **Fixed times win** — "at 4 PM" / "9–10" is anchored; everything else flows around it.
2. **Your order is respected** — "X then Y then Z" is placed as a true forward timeline.
3. **Smart priority fills the rest** — tasks with no time/order are ranked, and hard tasks go into peak-focus hours.
4. **Durations** — explicit time/range wins; otherwise Hard = 1h 30m, Normal = 1h, Easy = 45m.
5. **No collisions** — flexible tasks never overlap your fixed events; if something can't fit before a fixed block, it's placed after.

---

## Architecture

Clutch is an **agentic pipeline** built with LangGraph. The key design choice: the LLM handles *understanding language*, while the *planning math is deterministic* — so results are explainable, consistent, and never hallucinated.

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

The full priority/schedule logic is **mirrored in the browser** (`frontend/src/planner.js`), so edits and reorders re-plan instantly with no server round-trip.

---

## Tech stack

- **Frontend:** React + Vite
- **Backend:** FastAPI + LangGraph
- **LLM:** provider-switchable — Groq (`qwen/qwen3-32b`, default) or Google Gemini (`gemini-2.0-flash`), via one env var
- **Deployment:** a single Docker container (FastAPI serves the built React app + the API), hosted on Render

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

## Deploy (Render)

One container builds the frontend and serves it from FastAPI alongside the API.

1. Push the repo to GitHub.
2. Render → **New Web Service** → connect the repo → Runtime **Docker**, Instance **Free**.
3. Add env vars: `LLM_PROVIDER=groq`, `GROQ_MODEL=qwen/qwen3-32b`, `GROQ_API_KEY=...`
4. **Create Web Service** → get a public `https://…onrender.com` URL.

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
