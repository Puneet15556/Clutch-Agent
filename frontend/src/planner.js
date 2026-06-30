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
  const out = tasks.map((t) => {
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
  out.sort((a, b) => b.priority_score - a.priority_score);
  return out;
}

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
  tasks.forEach((t) => {
    const dur = parseInt(t.est_minutes) || 60;
    if (!t.deadline) assumptions.push(`No deadline given for “${t.title}” — treated as flexible.`);
    const from = t.difficulty === "Hard" ? ps : wake;
    let start = nextFree(from, dur);
    if (start === null) start = nextFree(wake, dur);
    if (start === null) {
      schedule.push({ task: t.title, slot: null, note: "No room left today — carried to tomorrow." });
      assumptions.push(`“${t.title}” didn't fit today; carried to tomorrow.`);
      return;
    }
    const end = start + dur;
    busy.push([start, end]);
    schedule.push({
      task: t.title, category: t.category, difficulty: t.difficulty,
      slot: `${toHHMM(start)}–${toHHMM(end)}`, reason: t.reason, fixed: false,
    });
  });

  schedule.push(...fixedEntries);
  schedule.sort((a, b) => (a.slot || "99:99").localeCompare(b.slot || "99:99"));
  return { schedule, assumptions };
}

function dt(hhmm) {
  const d = new Date();
  const stamp = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
  const [h, m] = hhmm.split(":");
  return `${stamp}T${h.padStart(2, "0")}${m.padStart(2, "0")}00`;
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
