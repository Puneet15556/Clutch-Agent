"""
LangGraph planner agent.

Flow:
    parse  -->  (clarify?)  -->  enrich  -->  prioritize  -->  schedule  --> END
                   |
                   +--> clarify (END, user se sawaal poochho)

- parse / enrich  : Gemini karta hai (samajhna)
- prioritize / schedule : Python karta hai (deterministic + explainable)
"""
import json
from datetime import datetime, date

from langgraph.graph import StateGraph, END

from .state import PlannerState, ParsedTasks, CATEGORIES
from .llm import get_llm


# ----------------------------------------------------------------------------
# NODE 1 — parse: brain-dump se structured tasks nikaalo
# ----------------------------------------------------------------------------
def parse_node(state: PlannerState) -> dict:
    llm = get_llm()
    structured = llm.with_structured_output(ParsedTasks)
    today = date.today().isoformat()
    prompt = (
        f"Today's date is {today}. Extract a list of tasks from the user's message below. "
        f"Read their own words carefully and capture, per task:\n"
        f"- title: short and clear — do NOT include the time or date words in the title "
        f"(e.g. 'Driving at 4 PM' -> title 'Driving')\n"
        f"- at_time: if the user named a specific clock time OR a time range (e.g. 'at 4 PM' -> '16:00', "
        f"'9am' -> '09:00', '9-10' -> '09:00'), output the START as 'HH:MM' 24-hour; otherwise null\n"
        f"- order: if the user explicitly states a sequence (words like 'then', 'first', "
        f"'after that', 'next', or a numbered list), number the tasks 1,2,3... in that stated "
        f"sequence; if the tasks are just listed with no ordering intent, leave order null\n"
        f"- deadline: ISO 'YYYY-MM-DD' if a date/day is mentioned (resolve 'today', 'tomorrow', "
        f"'Friday' relative to today's date); otherwise null\n"
        f"- est_minutes: the duration in minutes ONLY if the user states a duration or a time range "
        f"(e.g. '2 hours' -> 120, '45 min' -> 45, a range '9-10' -> 60); otherwise null\n"
        f"- importance: low | medium | high — infer from cues like 'urgent', 'important', 'must', "
        f"'critical', 'do this first' (default medium)\n"
        f"- difficulty: Easy | Normal | Hard — ONLY set this if the user signals it "
        f"(e.g. 'this is hard for me', 'tough', 'easy', 'quick'); otherwise leave it null\n\n"
        f"User message:\n{state['raw_input']}"
    )
    result = structured.invoke(prompt)
    return {"tasks": [t.model_dump() for t in result.tasks]}


# ----------------------------------------------------------------------------
# Conditional edge — agent proceeds on its own judgment; it only asks the user
# a question when the input was too vague to extract a single task.
# ----------------------------------------------------------------------------
def route_after_parse(state: PlannerState) -> str:
    if not state.get("tasks"):
        return "clarify"
    return "enrich"


def clarify_node(state: PlannerState) -> dict:
    return {
        "needs_clarification": True,
        "clarification": (
            "I couldn't find a clear task in that. Try describing what you need to do — "
            "for example: \"submit the report by Friday\" or \"pay the electricity bill today\"."
        ),
    }


# ----------------------------------------------------------------------------
# NODE 2 — enrich: category + personalized difficulty
# ----------------------------------------------------------------------------
def enrich_node(state: PlannerState) -> dict:
    tasks = state["tasks"]

    llm = get_llm()
    structured = llm.with_structured_output(ParsedTasks)
    prompt = (
        f"For each task below, fill ONLY the fields that are null:\n"
        f"- category: choose one of {CATEGORIES}\n"
        f"- difficulty: Easy / Normal / Hard, judged by the task's typical cognitive effort "
        f"and the time it usually demands\n"
        f"Keep every other field exactly the same.\n\n"
        f"Tasks JSON:\n{json.dumps(tasks, ensure_ascii=False)}"
    )
    result = structured.invoke(prompt)
    llm_tasks = [t.model_dump() for t in result.tasks]

    # Merge onto the ORIGINAL tasks: keep everything parse extracted (at_time, deadline,
    # est_minutes, importance, title) and only take category/difficulty from the LLM,
    # and only where the user hasn't already set them.
    merged = []
    for i, orig in enumerate(tasks):
        out = dict(orig)
        llm_t = llm_tasks[i] if i < len(llm_tasks) else {}
        if not out.get("category"):
            out["category"] = llm_t.get("category")
        if not out.get("difficulty"):
            out["difficulty"] = llm_t.get("difficulty")
        merged.append(out)
    return {"tasks": merged}


# ----------------------------------------------------------------------------
# NODE 3 — prioritize: urgency + importance + difficulty (Python, explainable)
# ----------------------------------------------------------------------------
def _urgency_score(deadline: str | None) -> int:
    if not deadline:
        return 1
    try:
        d = datetime.fromisoformat(deadline).date()
    except ValueError:
        return 1
    days = (d - date.today()).days
    if days <= 0:
        return 5
    if days == 1:
        return 4
    if days <= 3:
        return 3
    if days <= 7:
        return 2
    return 1


def prioritize_node(state: PlannerState) -> dict:
    imp_map = {"low": 1, "medium": 2, "high": 3}
    diff_map = {"Easy": 1, "Normal": 2, "Hard": 3}
    tasks = state["tasks"]
    for t in tasks:
        u = _urgency_score(t.get("deadline"))
        i = imp_map.get((t.get("importance") or "medium").lower(), 2)
        d = diff_map.get(t.get("difficulty") or "Normal", 2)
        t["priority_score"] = round(u * 2 + i * 1.5 + d, 1)
        t["reason"] = (
            f"Urgency {u}/5, importance {i}/3, "
            f"difficulty {t.get('difficulty', 'Normal')} — hence this position."
        )
    # No sorting here — schedule_node decides final order (fixed time > user order > priority).
    return {"tasks": tasks}


# ----------------------------------------------------------------------------
# NODE 4 — schedule: energy-aware time-blocking (Python)
# ----------------------------------------------------------------------------
# Default duration by difficulty — used ONLY when the user gave no duration/time.
DIFF_MINUTES = {"Easy": 45, "Normal": 60, "Hard": 90}


def _duration(t: dict) -> int:
    if t.get("est_minutes"):
        return int(t["est_minutes"])
    return DIFF_MINUTES.get(t.get("difficulty") or "Normal", 60)


def _to_min(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _to_hhmm(mins: int) -> str:
    return f"{mins // 60:02d}:{mins % 60:02d}"


def _peak_window(profile: dict) -> tuple[int, int]:
    peak = (profile.get("peak") or "morning").lower()
    return {
        "morning": (_to_min("09:00"), _to_min("12:00")),
        "afternoon": (_to_min("13:00"), _to_min("17:00")),
        "evening": (_to_min("18:00"), _to_min("22:00")),
        "night": (_to_min("21:00"), _to_min("23:30")),
    }.get(peak, (_to_min("09:00"), _to_min("12:00")))


def schedule_node(state: PlannerState) -> dict:
    profile = state.get("profile", {})
    assumptions: list[str] = []

    if not profile.get("wake") or not profile.get("sleep"):
        assumptions.append("Used a default day window (08:00–23:00) since wake/sleep times weren't given.")

    wake = _to_min(profile.get("wake", "08:00"))
    sleep = _to_min(profile.get("sleep", "23:00"))
    peak_start, _ = _peak_window(profile)

    # Fixed blocks become "busy" intervals AND show up on the timeline.
    busy = []
    fixed_entries = []
    for fb in profile.get("fixed_blocks", []):
        s, e = _to_min(fb["start"]), _to_min(fb["end"])
        label = fb.get("label", "Fixed")
        busy.append((s, e, label))
        fixed_entries.append({"task": label, "slot": f"{_to_hhmm(s)}–{_to_hhmm(e)}", "fixed": True})

    def overlaps(s: int, e: int) -> bool:
        return any(s < be and e > bs for bs, be, _ in busy)

    def next_free(start_from: int, dur: int) -> int | None:
        cur = max(start_from, wake)
        while cur + dur <= sleep:
            if not overlaps(cur, cur + dur):
                return cur
            # jump to where the overlapping block ends
            cur = max([be for bs, be, _ in busy if cur < be and cur + dur > bs] + [cur + 15])
        return None

    schedule = []
    tasks = state["tasks"]

    def add(t: dict, start: int, reason: str) -> None:
        dur = _duration(t)
        end = start + dur
        busy.append((start, end, t["title"]))
        schedule.append({
            "task": t["title"], "category": t.get("category"), "difficulty": t.get("difficulty"),
            "slot": f"{_to_hhmm(start)}–{_to_hhmm(end)}", "reason": reason, "fixed": False,
        })

    def flow(t: dict, respect_peak: bool = True) -> None:
        dur = _duration(t)
        if not t.get("deadline"):
            assumptions.append(f"No deadline given for “{t['title']}” — treated as flexible.")
        # Hard tasks prefer the peak window — but only when we're free to reorder.
        # If you gave an explicit sequence, your order wins over energy optimization.
        search_from = peak_start if (respect_peak and t.get("difficulty") == "Hard") else wake
        start = next_free(search_from, dur) or next_free(wake, dur)
        if start is None:
            schedule.append({"task": t["title"], "slot": None,
                             "note": "No room left today — carried to tomorrow."})
            assumptions.append(f"“{t['title']}” didn't fit today; carried to tomorrow.")
            return
        add(t, start, t.get("reason"))

    # Phase 1: tasks with an explicit clock time are anchored exactly there.
    for t in tasks:
        if t.get("at_time"):
            try:
                add(t, _to_min(t["at_time"]), f"Fixed time you set ({t['at_time']}).")
            except (ValueError, AttributeError):
                flow(t)

    # Phase 2: tasks you gave an explicit order — placed in that sequence (order > peak).
    for t in sorted((x for x in tasks if not x.get("at_time") and x.get("order") is not None),
                    key=lambda x: x["order"]):
        flow(t, respect_peak=False)

    # Phase 3: everything else — smart-prioritized (highest score first).
    for t in sorted((x for x in tasks if not x.get("at_time") and x.get("order") is None),
                    key=lambda x: x.get("priority_score") or 0, reverse=True):
        flow(t)

    schedule += fixed_entries
    schedule.sort(key=lambda s: s["slot"] or "99:99")

    # Reorder the task list to match the schedule so the cards and timeline agree.
    slot_start = {s["task"]: _to_min(s["slot"].split("–")[0]) for s in schedule if s.get("slot")}
    tasks_sorted = sorted(tasks, key=lambda t: slot_start.get(t["title"], 9999))
    return {"schedule": schedule, "assumptions": assumptions, "tasks": tasks_sorted}


# ----------------------------------------------------------------------------
# Graph build
# ----------------------------------------------------------------------------
def build_graph():
    g = StateGraph(PlannerState)
    g.add_node("parse", parse_node)
    g.add_node("clarify", clarify_node)
    g.add_node("enrich", enrich_node)
    g.add_node("prioritize", prioritize_node)
    g.add_node("schedule", schedule_node)

    g.set_entry_point("parse")
    g.add_conditional_edges("parse", route_after_parse,
                            {"clarify": "clarify", "enrich": "enrich"})
    g.add_edge("clarify", END)
    g.add_edge("enrich", "prioritize")
    g.add_edge("prioritize", "schedule")
    g.add_edge("schedule", END)
    return g.compile()


def build_replan_graph():
    """parse skip — frontend se aayi (user-edited) task list pe seedha
    enrich -> prioritize -> schedule chalata hai."""
    g = StateGraph(PlannerState)
    g.add_node("enrich", enrich_node)
    g.add_node("prioritize", prioritize_node)
    g.add_node("schedule", schedule_node)
    g.set_entry_point("enrich")
    g.add_edge("enrich", "prioritize")
    g.add_edge("prioritize", "schedule")
    g.add_edge("schedule", END)
    return g.compile()
