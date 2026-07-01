import { useState, useEffect } from "react";
import { plan } from "./api";
import { prioritize, scheduleDay, buildIcs, googleCalUrl } from "./planner";
import "./App.css";

// Difficulty options — clean, professional labels
const DIFFICULTY = [
  { key: "Easy", label: "Easy", dot: "#22c55e" },
  { key: "Normal", label: "Normal", dot: "#eab308" },
  { key: "Hard", label: "Hard", dot: "#ef4444" },
];
const IMPORTANCE = [
  { key: "low", label: "Low" },
  { key: "medium", label: "Medium" },
  { key: "high", label: "High" },
];
const CATEGORIES = ["Study", "Coding/DSA", "Admin/Bills", "Meetings", "Personal/Health", "Creative"];

const DEFAULT_PROFILE = {
  wake: "07:00",
  sleep: "23:30",
  peak: "morning",
  fixed_blocks: [],
};

export default function App() {
  const [raw, setRaw] = useState("");
  const [profile, setProfile] = useState(() =>
    JSON.parse(localStorage.getItem("profile") || "null") || DEFAULT_PROFILE
  );
  const [tasks, setTasks] = useState([]);
  const [schedule, setSchedule] = useState([]);
  const [assumptions, setAssumptions] = useState([]);
  const [ics, setIcs] = useState("");
  const [clarify, setClarify] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Progress tracking
  const [xp, setXp] = useState(() => +(localStorage.getItem("xp") || 0));
  const level = Math.floor(xp / 100) + 1;
  const xpInLevel = xp % 100;

  useEffect(() => localStorage.setItem("profile", JSON.stringify(profile)), [profile]);
  useEffect(() => localStorage.setItem("xp", xp), [xp]);

  async function runPlan() {
    setLoading(true); setError(""); setClarify("");
    try {
      const res = await plan(raw, profile);
      if (res.needs_clarification) {
        setClarify(res.clarification); setTasks([]); setSchedule([]); setAssumptions([]); setIcs("");
      } else {
        setTasks(res.tasks || []); setSchedule(res.schedule || []);
        setAssumptions(res.assumptions || []); setIcs(res.ics || "");
      }
    } catch (e) { setError(String(e)); }
    setLoading(false);
  }

  // Download the schedule as an .ics file (opens in any calendar app, includes an alarm)
  function downloadCalendar() {
    const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "clutch.ics"; a.click();
    URL.revokeObjectURL(url);
  }

  // User edited difficulty / importance -> re-plan instantly in the browser (no LLM, no rate limit)
  function editTask(idx, field, value) {
    const edited = tasks.map((t, i) => (i === idx ? { ...t, [field]: value } : t));
    const scored = prioritize(edited);
    const { schedule: sch, assumptions: asm, tasks: ordered } = scheduleDay(scored, profile);
    setTasks(ordered);
    setSchedule(sch);
    setAssumptions(asm);
    setIcs(buildIcs(sch));
  }

  // Complete a task -> award points and remove it
  function completeTask(idx) {
    const t = tasks[idx];
    let gained = 10;
    if (t.deadline && new Date(t.deadline) >= new Date()) gained += 5; // early-finish bonus
    setXp((x) => x + gained);
    setTasks(tasks.filter((_, i) => i !== idx));
    setSchedule(schedule.filter((s) => s.task !== t.title));
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="mark">C</span>
          <div className="brand-text">
            <span className="name">Clutch</span>
            <span className="tagline">your AI deadline agent</span>
          </div>
        </div>
        <div className="progress">
          <span className="level">Level {level}</span>
          <div className="track"><div className="fill" style={{ width: `${xpInLevel}%` }} /></div>
          <span className="points">{xp} pts</span>
        </div>
      </header>

      {/* Profile */}
      <section className="card">
        <h2 className="card-title">Your routine</h2>
        <p className="card-sub">Used to build a schedule that fits your day.</p>

        <div className="field-row">
          <label className="field">
            <span>Wake up</span>
            <input type="time" value={profile.wake}
              onChange={(e) => setProfile({ ...profile, wake: e.target.value })} />
          </label>

          <label className="field">
            <span>Sleep</span>
            <input type="time" value={profile.sleep}
              onChange={(e) => setProfile({ ...profile, sleep: e.target.value })} />
          </label>

          <label className="field">
            <span>Peak focus</span>
            <select value={profile.peak}
              onChange={(e) => setProfile({ ...profile, peak: e.target.value })}>
              <option value="morning">Morning</option>
              <option value="afternoon">Afternoon</option>
              <option value="evening">Evening</option>
              <option value="night">Night</option>
            </select>
          </label>
        </div>

      </section>

      {/* Input */}
      <section className="card">
        <h2 className="card-title">What's on your plate?</h2>
        <p className="card-sub">
          Describe everything in plain language — mention deadlines, how long something takes,
          what's urgent, or what feels hard. The agent reads those cues and plans accordingly.
        </p>

        <textarea value={raw} onChange={(e) => setRaw(e.target.value)}
          placeholder={"e.g. Finish the DSA assignment by Friday — it's hard for me and high priority.\nPay rent today, quick.\nPrep about 2 hours for the interview tomorrow."} />

        <button className="primary" disabled={loading || !raw.trim()} onClick={runPlan}>
          {loading ? "Planning…" : "Plan my day"}
        </button>

        {error && <p className="error">{error}</p>}
        {clarify && <div className="notice">{clarify}</div>}
      </section>

      {/* Tasks */}
      {tasks.length > 0 && (
        <section className="card">
          <h2 className="card-title">Tasks</h2>
          <p className="card-sub">Ordered by priority. Adjust difficulty or importance — it re-plans instantly.</p>

          <div className="task-list">
            {tasks.map((t, i) => (
              <div className="task" key={i}>
                <div className="task-top">
                  <span className="task-title">{t.title}</span>
                  <button className="ghost" onClick={() => completeTask(i)}>Mark done</button>
                </div>

                <div className="task-meta">
                  {t.deadline && <span className="meta-pill">Due {t.deadline}</span>}
                  {t.category && <span className="meta-pill">{t.category}</span>}
                </div>

                <div className="controls">
                  <div className="control">
                    <span className="control-label">Difficulty</span>
                    <div className="segmented">
                      {DIFFICULTY.map((d) => (
                        <button key={d.key}
                          className={t.difficulty === d.key ? "seg active" : "seg"}
                          onClick={() => editTask(i, "difficulty", d.key)}>
                          <i className="dot" style={{ background: d.dot }} />{d.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="control">
                    <span className="control-label">Importance</span>
                    <div className="segmented">
                      {IMPORTANCE.map((m) => (
                        <button key={m.key}
                          className={t.importance === m.key ? "seg active" : "seg"}
                          onClick={() => editTask(i, "importance", m.key)}>{m.label}</button>
                      ))}
                    </div>
                  </div>
                </div>

                {t.reason && <p className="reason">{t.reason}</p>}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Schedule */}
      {schedule.length > 0 && (
        <section className="card">
          <div className="card-head">
            <h2 className="card-title">Today's schedule</h2>
            {ics && <button className="ghost" onClick={downloadCalendar}>Add all to calendar</button>}
          </div>

          <div className="timeline">
            {schedule.map((s, i) => (
              <div className={s.fixed ? "slot fixed" : "slot"} key={i}>
                <span className="slot-time">{s.slot || "—"}</span>
                <span className="slot-task">
                  {s.task}{s.fixed && <span className="slot-tag">Fixed</span>}
                </span>
                {s.note && <span className="slot-note">{s.note}</span>}
                {!s.fixed && s.slot && (
                  <a className="gcal" href={googleCalUrl(s)} target="_blank" rel="noopener noreferrer">
                    + Google Calendar
                  </a>
                )}
              </div>
            ))}
          </div>

          {assumptions.length > 0 && (
            <div className="assumptions">
              <span className="assumptions-title">What the agent assumed</span>
              <ul>
                {assumptions.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
