# Deadline Agent — Backend (FastAPI + LangGraph + Gemini)

AI productivity planner agent. Brain-dump do, agent usko **categorize → personalize difficulty → prioritize → energy-aware schedule** karke deta hai.

## Architecture (LangGraph)

```
parse ──(profile missing?)──> clarify (END: user se sawaal)
   │
   └──> enrich ──> prioritize ──> schedule ──> END
```

- **parse / enrich** → Gemini (`gemini-2.0-flash`) karta hai
- **prioritize / schedule** → Python (deterministic + explainable)

## Local mein chalao

```bash
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# key daalo
copy .env.example .env      # phir .env mein apni GEMINI_API_KEY likho

uvicorn app.main:app --reload
```

Khulega: http://127.0.0.1:8000/docs (Swagger UI — yahin test karo)

## Test request

`POST /plan`
```json
{
  "raw_input": "Kal tak DSA practice karni hai, Friday tak assignment, aur aaj rent bharna hai",
  "profile": {
    "wake": "07:00",
    "sleep": "23:30",
    "peak": "morning",
    "fixed_blocks": [{"start": "09:00", "end": "13:00", "label": "College"},
                     {"start": "18:00", "end": "19:00", "label": "Gym"}],
    "hard_categories": ["Coding/DSA"]
  }
}
```

Agar `profile` khaali bhejo to agent `clarification` sawaal wapas karega (proactive agentic behaviour).

## Deploy (Google Cloud Run)

Dockerfile aayega — `gcloud run deploy` se live.
