# Deadline Agent — Project Description

> Copy this into a Google Doc, set sharing to "Anyone with the link", and submit that link.

## Problem Statement Selected

**Problem Statement 1 — The Last-Minute Life Saver.** Students and professionals miss deadlines because traditional reminder apps are passive — they nudge, but they don't help you actually plan and act. We set out to build an AI companion that proactively plans, prioritizes, and schedules so tasks get done before they slip.

## Solution Overview

Deadline Agent takes a plain-language brain-dump of everything on your plate and turns it into a prioritized, time-blocked day. An agentic pipeline (built on LangGraph) reads your words to extract deadlines, durations, importance, and difficulty; then deterministically scores priority and lays out a schedule that respects your sleep, fixed commitments, and peak-focus hours. It explains its reasoning, shows the assumptions it made, lets you adjust any task and re-plan instantly, and exports the day to your calendar with alarms.

## Key Features

- **Natural-language task capture** — no forms; the agent reads cues like "hard for me", "urgent", "today", "2 hours".
- **Autonomous prioritization** — combines deadline urgency, importance, and difficulty into an explainable score.
- **Energy-aware scheduling** — places hard tasks in your peak-focus window and works around fixed commitments.
- **Transparent assumptions** — the agent reports every guess it made.
- **Instant re-planning** — change difficulty/importance and the day re-orders in the browser, with no server round-trip.
- **Calendar export with reminders** — one-click `.ics` download with alarms (Google/Apple/Outlook).
- **Gamification** — points and levels for completing tasks on time.

## Technologies Used

- Frontend: React, Vite
- Backend: FastAPI, LangGraph (agent orchestration)
- LLM: provider-switchable (Groq / Google Gemini)
- Deterministic planning engine in Python (and mirrored in JavaScript for instant client-side re-planning)

## Google Technologies Utilized

- **Google Cloud Run** — the application is deployed as a containerized service on Cloud Run.
- **Google Cloud Build** — builds the container image from source during deployment.
- **Google Gemini (supported)** — the LLM layer is provider-switchable and integrates Google Gemini (`gemini-2.0-flash`) via `langchain-google-genai`; the architecture runs on Gemini by flipping a single environment variable.
