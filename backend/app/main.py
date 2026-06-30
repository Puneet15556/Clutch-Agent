"""FastAPI app — serves the planning API and (in the deployed container) the React app."""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .graph import build_graph, build_replan_graph
from .ics_export import build_ics

app = FastAPI(title="Clutch API")

# frontend (React) ke liye CORS khol do — hackathon ke liye sab allow
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()
replan_graph = build_replan_graph()


class PlanRequest(BaseModel):
    raw_input: str
    profile: dict = {}   # {wake, sleep, peak, fixed_blocks, hard_categories}


class ReplanRequest(BaseModel):
    tasks: list = []      # user-edited tasks (difficulty/category user ne chuna ho sakta)
    profile: dict = {}


@app.get("/health")
def health():
    return {"ok": True}


def _run(compiled, payload):
    """Run a graph and turn model/quota failures into a clean, readable error."""
    try:
        result = compiled.invoke(payload)
    except Exception as e:
        msg = str(e)
        if "RESOURCE_EXHAUSTED" in msg or "429" in msg or "rate limit" in msg.lower():
            raise HTTPException(
                status_code=429,
                detail="Model quota / rate limit hit for the current API key. "
                       "Wait a moment and retry, or swap the key in backend/.env.",
            )
        raise HTTPException(status_code=502, detail=f"Planning failed: {msg}")
    result["ics"] = build_ics(result.get("schedule", []))
    return result


@app.post("/plan")
def plan(req: PlanRequest):
    """Brain-dump + profile -> categorized, prioritized, scheduled plan."""
    return _run(graph, {"raw_input": req.raw_input, "profile": req.profile})


@app.post("/replan")
def replan(req: ReplanRequest):
    """User-edited task list (difficulty/category set) -> re-plan, skipping parse."""
    return _run(replan_graph, {"tasks": req.tasks, "profile": req.profile})


# --- Serve the built React app (only present in the deployed container) -------
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
