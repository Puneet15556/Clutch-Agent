"""Data models + LangGraph state ka shape."""
from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field

# 6 fixed categories — list badhao mat (scope creep se bachne ke liye)
CATEGORIES = ["Study", "Coding/DSA", "Admin/Bills", "Meetings", "Personal/Health", "Creative"]


class Task(BaseModel):
    title: str
    deadline: Optional[str] = Field(None, description="ISO date 'YYYY-MM-DD' agar pata ho, warna null")
    est_minutes: int = Field(60, description="Estimated time in minutes (guess karo)")
    importance: str = Field("medium", description="low | medium | high")
    at_time: Optional[str] = Field(
        None,
        description="Specific start time as 'HH:MM' 24-hour, ONLY if the user named a clock time "
                    "(e.g. 'at 4 PM' -> '16:00', '9am' -> '09:00'); otherwise null",
    )
    order: Optional[int] = Field(
        None,
        description="Sequence number 1,2,3... ONLY if the user explicitly stated an order "
                    "(words like 'then', 'first', 'after that', 'next', or a numbered list). "
                    "If tasks are just listed with no ordering intent, leave null.",
    )
    category: Optional[str] = Field(None, description=f"In mein se ek: {CATEGORIES}")
    difficulty: Optional[str] = Field(None, description="Easy | Normal | Hard")
    # ye fields backend khud bharta hai:
    priority_score: Optional[float] = None
    reason: Optional[str] = None


class ParsedTasks(BaseModel):
    """Gemini ka structured output wrapper."""
    tasks: List[Task]


class PlannerState(TypedDict, total=False):
    """Graph ki shared memory — har node isme padhta/likhta hai."""
    raw_input: str        # user ka brain-dump
    profile: dict         # {wake, sleep, peak, fixed_blocks, hard_categories}
    tasks: list           # list[dict] — parse/enrich/prioritize isko bharte hain
    schedule: list        # final time-blocked plan
    assumptions: list     # reasoned guesses the agent made (transparency)
    needs_clarification: bool
    clarification: str    # only when input is too vague to extract any task
