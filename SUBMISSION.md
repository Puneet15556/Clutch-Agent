# Clutch — Project Description

> Copy everything below into a Google Doc, add your live link at the top, then set sharing to **"Anyone with the link → Viewer"** and submit that link.

**Project name:** Clutch — your AI deadline agent
**Live application (Google Cloud Run):** _<paste your URL>_
**GitHub repository:** _<paste your repo link>_

---

## Problem Statement Selected

**Problem Statement 1 — The Last-Minute Life Saver.**

Students, professionals, and entrepreneurs miss deadlines not for lack of reminders, but because existing tools are *passive*. A reminder tells you *that* something is due; it does nothing to help you decide what to tackle first, estimate how long it takes, or fit it into a realistic day. The outcome is the familiar last-minute scramble. We set out to build an AI companion that moves beyond reminders and actively helps users **plan, prioritize, and complete** their work before deadlines slip.

## Solution Overview

**Clutch** is an AI agent that does the planning for you. You describe everything on your plate in plain, natural language — Clutch reads it, extracts the important details, prioritizes intelligently, and produces an hour-by-hour schedule that fits your real day (sleep, fixed commitments, and your peak-focus hours). Crucially, it is **transparent**: it explains why each task is ranked where it is and surfaces every assumption it made, so the user stays in control.

Under the hood, Clutch is an **agentic pipeline** built on LangGraph. We made a deliberate architectural choice: the language model handles *understanding* (reading messy human input), while the *planning logic is deterministic* (priority scoring and time-blocking in code). This keeps the agent's decisions explainable, consistent, and free of hallucination — a planner you can actually trust.

## Key Features

- **Natural-language task capture** — no forms; the agent reads cues like "hard for me", "urgent", "today", or "2 hours" directly from a sentence.
- **Autonomous prioritization** — combines deadline urgency, stated importance, and difficulty into a transparent priority score.
- **Energy-aware scheduling** — schedules hard tasks during the user's peak-focus window and automatically works around fixed commitments and sleep.
- **Explainable reasoning + assumptions** — every ranking comes with a reason, and the agent reports the assumptions it made when information was missing.
- **Instant in-browser re-planning** — adjusting a task's difficulty or importance re-plans the whole day immediately, with no server round-trip.
- **Calendar export with reminders** — one click produces a standard `.ics` file with alarms, importable into Google Calendar, Apple Calendar, or Outlook.
- **Gamified progress** — points and levels reward completing tasks on time, encouraging follow-through.

## Technologies Used

- **Frontend:** React, Vite
- **Backend:** FastAPI, LangGraph (agent orchestration)
- **AI / LLM:** a provider-switchable layer integrating Groq and Google Gemini
- **Planning engine:** deterministic Python logic, mirrored in JavaScript for instant client-side re-planning
- **Containerization:** Docker (single image serving both API and frontend)

## Google Technologies Utilized

- **Google Cloud Run** — the application is deployed as a containerized, publicly accessible service on Cloud Run.
- **Google Cloud Build** — builds the container image directly from the source repository during deployment.
- **Google Gemini** — the LLM layer integrates Google Gemini (`gemini-2.0-flash`) via the `langchain-google-genai` SDK; the agent runs on Gemini by setting a single environment variable, demonstrating first-class Gemini support in the architecture.

## What Makes Clutch Different

Most "AI to-do" apps are a thin wrapper around a single prompt. Clutch is a genuine **multi-step agent**: it reads language, makes its own reasoned decisions when information is missing, prioritizes, schedules around real-world constraints, and explains itself — then hands you a calendar you can act on. The separation of *AI understanding* from *deterministic planning* makes it both smart and reliable, which is exactly what a "last-minute life saver" needs to be.
