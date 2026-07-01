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

- **Natural-language task capture** — no forms; the agent reads cues like "hard for me", "urgent", "today", "9–10", or "2 hours" directly from a sentence.
- **Fixed clock times** — "gym at 6 PM" or "DSA 9–10" is anchored to that exact slot; everything else flows around it.
- **Respects your order** — "X then Y then Z" is scheduled as a true forward sequence; a plain list is smart-prioritized instead.
- **Smart, explainable prioritization** — combines deadline urgency, importance, and difficulty into a transparent score, with hard tasks placed in peak-focus hours.
- **Difficulty-based durations** — when no time is given, Hard = 1h 30m, Normal = 1h, Easy = 45m; an explicit time or range overrides this.
- **Manual reorder** — up/down arrows on each task instantly re-plan the day (durations kept, times recomputed).
- **Instant in-browser re-planning** — editing difficulty, importance, or order never waits on the server.
- **Transparent assumptions** — every ranking has a reason, and the agent reports the guesses it made when information was missing.
- **Google Calendar integration** — "Add all to calendar" downloads an `.ics` with 10-minute reminder alarms; each task also has a one-click "+ Google Calendar" quick-add.
- **Gamified progress** — points and levels reward completing tasks on time.

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
