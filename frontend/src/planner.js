// Deterministic planner — mirrors the backend's prioritize/schedule/ICS logic.
// Runs in the browser so edits re-plan instantly with no server call.

const IMP = { low: 1, medium: 2, high: 3 };
const DIF = { Easy: 1, Normal: 2, Hard: 3 };

function urgency(deadline) {
  if (!deadline) return 1;
  const d = new Date(deadline + "T00:00:00");
  if (isNaN(d)) return 1;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const days = Math.round((d - today) / 86400000);
  if (days <= 0) return 5;
  if (days === 1) return 4;
  if (days <= 3) return 3;
  if (days <= 7) return 2;
  return 1;
}

export function prioritize(tasks) {
  // No sorting here — scheduleDay decides final order (fixed time > user order > priority).
  return tasks.map((t) => {
    const u = urgency(t.deadline);
    const i = IMP[(t.importance || "medium").toLowerCase()] ?? 2;
    const d = DIF[t.difficulty || "Normal"] ?? 2;
    const score = Math.round((u * 2 + i * 1.5 + d) * 10) / 10;
    return {
      ...t,
      priority_score: score,
      reason: `Urgency ${u}/5, importance ${i}/3, difficulty ${t.difficulty || "Normal"} — hence this position.`,
    };
  });
}

// Default duration by difficulty — used ONLY when the user gave no duration/time.
const DIFF_MINUTES = { Easy: 45, Normal: 60, Hard: 90 };
const durationOf = (t) => (t.est_minutes ? parseInt(t.est_minutes) : (DIFF_MINUTES[t.difficulty || "Normal"] ?? 60));

const toMin = (hhmm) => { const [h, m] = hhmm.split(":").map(Number); return h * 60 + m; };
const toHHMM = (m) => `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
const peakStart = (peak) => ({
  morning: 540, afternoon: 780, evening: 1080, night: 1260,
}[(peak || "morning").toLowerCase()] ?? 540);

export function scheduleDay(tasks, profile) {
  const assumptions = [];
  if (!profile.wake || !profile.sleep)
    assumptions.push("Used a default day window (08:00–23:00) since wake/sleep times weren't given.");

  const wake = toMin(profile.wake || "08:00");
  const sleep = toMin(profile.sleep || "23:00");
  const ps = peakStart(profile.peak);

  const busy = [];
  const fixedEntries = [];
  (profile.fixed_blocks || []).forEach((fb) => {
    const s = toMin(fb.start), e = toMin(fb.end);
    busy.push([s, e]);
    fixedEntries.push({ task: fb.label || "Fixed", slot: `${toHHMM(s)}–${toHHMM(e)}`, fixed: true });
  });

  const overlaps = (s, e) => busy.some(([bs, be]) => s < be && e > bs);
  const nextFree = (from, dur) => {
    let cur = Math.max(from, wake);
    while (cur + dur <= sleep) {
      if (!overlaps(cur, cur + dur)) return cur;
      const ends = busy.filter(([bs, be]) => cur < be && cur + dur > bs).map(([, be]) => be);
      cur = Math.max(...ends, cur + 15);
    }
    return null;
  };

  const schedule = [];

  const add = (t, start, reason) => {
    const dur = durationOf(t);
    const end = start + dur;
    busy.push([start, end]);
    schedule.push({
      task: t.title, category: t.category, difficulty: t.difficulty,
      slot: `${toHHMM(start)}–${toHHMM(end)}`, reason, fixed: false,
    });
  };

  const flow = (t, respectPeak = true) => {
    const dur = durationOf(t);
    if (!t.deadline) assumptions.push(`No deadline given for “${t.title}” — treated as flexible.`);
    const from = respectPeak && t.difficulty === "Hard" ? ps : wake;
    let start = nextFree(from, dur);
    if (start === null) start = nextFree(wake, dur);
    if (start === null) {
      schedule.push({ task: t.title, slot: null, note: "No room left today — carried to tomorrow." });
      assumptions.push(`“${t.title}” didn't fit today; carried to tomorrow.`);
      return;
    }
    add(t, start, t.reason);
  };

  // Phase 1: reserve fixed clock-time tasks exactly where they belong.
  const atStart = new Map();
  tasks.forEach((t) => {
    if (!t.at_time) return;
    const start = toMin(t.at_time);
    add(t, start, `Fixed time you set (${t.at_time}).`);
    atStart.set(t, start);
  });

  // Phase 2: explicit order as a TRUE forward sequence; fixed times push the cursor
  // forward so later tasks land after them instead of filling earlier gaps.
  let cursor = wake;
  tasks.filter((t) => t.order != null).sort((a, b) => a.order - b.order).forEach((t) => {
    const dur = durationOf(t);
    if (atStart.has(t)) { cursor = Math.max(cursor, atStart.get(t) + dur); return; }
    const start = nextFree(cursor, dur);
    if (start === null) {
      schedule.push({ task: t.title, slot: null, note: "No room left today — carried to tomorrow." });
      assumptions.push(`“${t.title}” didn't fit today; carried to tomorrow.`);
      return;
    }
    add(t, start, t.reason);
    cursor = start + dur;
  });

  // Phase 3: no order and no fixed time — smart-prioritized into remaining gaps.
  tasks.filter((t) => t.order == null && !t.at_time).sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0)).forEach((t) => flow(t, true));

  schedule.push(...fixedEntries);
  schedule.sort((a, b) => (a.slot || "99:99").localeCompare(b.slot || "99:99"));

  // Reorder tasks to match the schedule so cards and timeline agree.
  const slotStart = {};
  schedule.forEach((s) => { if (s.slot) slotStart[s.task] = toMin(s.slot.split("–")[0]); });
  const tasksSorted = [...tasks].sort((a, b) => (slotStart[a.title] ?? 9999) - (slotStart[b.title] ?? 9999));
  return { schedule, assumptions, tasks: tasksSorted };
}

function dt(hhmm) {
  const d = new Date();
  const stamp = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
  const [h, m] = hhmm.split(":");
  return `${stamp}T${h.padStart(2, "0")}${m.padStart(2, "0")}00`;
}

// One-click "Add to Google Calendar" link for a single scheduled task.
// Opens Google Calendar with the event pre-filled — no OAuth, no API needed.
export function googleCalUrl(slotItem) {
  if (!slotItem.slot) return null;
  const parts = slotItem.slot.replace("–", "-").split("-");
  if (parts.length !== 2) return null;
  const d = new Date();
  const day = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
  const fmt = (hhmm) => `${day}T${hhmm.trim().replace(":", "")}00`;
  const [start, end] = parts;
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: slotItem.task,
    dates: `${fmt(start)}/${fmt(end)}`,
    details: slotItem.reason || "Planned with Clutch",
    ctz: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

export function buildIcs(schedule) {
  const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Clutch//EN", "CALSCALE:GREGORIAN"];
  schedule.forEach((s, i) => {
    if (!s.slot) return;
    const parts = s.slot.replace("–", "-").split("-");
    if (parts.length !== 2) return;
    const [start, end] = parts.map((x) => x.trim());
    lines.push(
      "BEGIN:VEVENT",
      `UID:da-${i}-${dt(start).slice(0, 8)}@clutch`,
      `DTSTART:${dt(start)}`, `DTEND:${dt(end)}`,
      `SUMMARY:${s.task}`,
      `DESCRIPTION:${(s.reason || "").replace(/\n/g, " ")}`,
      "BEGIN:VALARM", "TRIGGER:-PT10M", "ACTION:DISPLAY",
      `DESCRIPTION:Reminder — ${s.task}`,
      "END:VALARM", "END:VEVENT",
    );
  });
  lines.push("END:VCALENDAR");
  return lines.join("\r\n");
}
