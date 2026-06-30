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
        f"- title: short and clear\n"
        f"- deadline: ISO 'YYYY-MM-DD' if a date/day is mentioned (resolve 'today', 'tomorrow', "
        f"'Friday' relative to today's date); otherwise null\n"
        f"- est_minutes: use any duration the user states (e.g. '2 hours' -> 120); otherwise a realistic estimate\n"
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

    # User ne jo manually choose kiya (category/difficulty), use yaad rakho —
    # AI ko sirf KHAALI fields bharne hain, user ki choice override NAHI karni.
    user_choice = [
        {"category": t.get("category"), "difficulty": t.get("difficulty")}
        for t in tasks
    ]

    llm = get_llm()
    structured = llm.with_structured_output(ParsedTasks)
    prompt = (
        f"For each task below, fill ONLY the fields that are null. Never change a field that "
        f"already has a value — the user (or earlier parsing) set it intentionally.\n"
        f"- category: choose one of {CATEGORIES}\n"
        f"- difficulty: Easy / Normal / Hard, judged by the task's typical cognitive effort "
        f"and the time it usually demands\n"
        f"Keep every other field exactly the same.\n\n"
        f"Tasks JSON:\n{json.dumps(tasks, ensure_ascii=False)}"
    )
    result = structured.invoke(prompt)
    enriched = [t.model_dump() for t in result.tasks]

    # Safety net: user ki manual choice wapas restore karo (AI galti se badle to bhi)
    for i, t in enumerate(enriched):
        if i < len(user_choice):
            if user_choice[i]["category"]:
                t["category"] = user_choice[i]["category"]
            if user_choice[i]["difficulty"]:
                t["difficulty"] = user_choice[i]["difficulty"]
    return {"tasks": enriched}


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
    tasks.sort(key=lambda x: x["priority_score"], reverse=True)
    return {"tasks": tasks}


# ----------------------------------------------------------------------------
# NODE 4 — schedule: energy-aware time-blocking (Python)
# ----------------------------------------------------------------------------
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
    for t in state["tasks"]:
        dur = int(t.get("est_minutes") or 60)
        if not t.get("deadline"):
            assumptions.append(f"No deadline given for “{t['title']}” — treated as flexible.")

        # Hard tasks start their search from the peak-focus window.
        search_from = peak_start if (t.get("difficulty") == "Hard") else wake
        start = next_free(search_from, dur) or next_free(wake, dur)
        if start is None:
            schedule.append({"task": t["title"], "slot": None,
                             "note": "No room left today — carried to tomorrow."})
            assumptions.append(f"“{t['title']}” didn't fit today; carried to tomorrow.")
            continue
        end = start + dur
        busy.append((start, end, t["title"]))
        schedule.append({
            "task": t["title"],
            "category": t.get("category"),
            "difficulty": t.get("difficulty"),
            "slot": f"{_to_hhmm(start)}–{_to_hhmm(end)}",
            "reason": t.get("reason"),
            "fixed": False,
        })

    schedule += fixed_entries
    schedule.sort(key=lambda s: s["slot"] or "99:99")
    return {"schedule": schedule, "assumptions": assumptions}


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
