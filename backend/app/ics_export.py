"""
Build a standard .ics calendar file from the schedule.

Each scheduled task becomes a VEVENT with a VALARM (alarm/reminder 10 minutes
before). The file imports into Google Calendar, Apple Calendar, or Outlook —
no OAuth, no external API.
"""
from datetime import date


def _dt(d: date, hhmm: str) -> str:
    h, m = hhmm.split(":")
    return f"{d.strftime('%Y%m%d')}T{int(h):02d}{int(m):02d}00"


def _split_slot(slot: str) -> tuple[str, str] | None:
    # slots use an en-dash: "09:00–10:30"
    parts = slot.replace("–", "-").split("-")
    if len(parts) != 2:
        return None
    return parts[0].strip(), parts[1].strip()


def build_ics(schedule: list) -> str:
    d = date.today()
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Deadline Agent//EN",
        "CALSCALE:GREGORIAN",
    ]
    for i, s in enumerate(schedule):
        slot = s.get("slot")
        if not slot:
            continue
        times = _split_slot(slot)
        if not times:
            continue
        start, end = times
        title = s.get("task", "Task")
        lines += [
            "BEGIN:VEVENT",
            f"UID:da-{i}-{d.strftime('%Y%m%d')}@deadline-agent",
            f"DTSTART:{_dt(d, start)}",
            f"DTEND:{_dt(d, end)}",
            f"SUMMARY:{title}",
            f"DESCRIPTION:{(s.get('reason') or '').replace(chr(10), ' ')}",
            "BEGIN:VALARM",
            "TRIGGER:-PT10M",
            "ACTION:DISPLAY",
            f"DESCRIPTION:Reminder — {title}",
            "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
