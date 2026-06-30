// Backend (FastAPI) request helpers.
// Dev: VITE_API_BASE points at the local backend. Prod: empty = same origin
// (FastAPI serves the frontend), so requests go to /plan, /replan directly.
const BASE = import.meta.env.VITE_API_BASE ?? "";

async function post(path, body) {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    let detail = await r.text();
    try { detail = JSON.parse(detail).detail || detail; } catch { /* keep raw text */ }
    throw new Error(detail);
  }
  return r.json();
}

// Brain-dump text se naya plan
export const plan = (raw_input, profile) => post("/plan", { raw_input, profile });

// User-edited task list (difficulty user ne chuni) se dobara plan
export const replan = (tasks, profile) => post("/replan", { tasks, profile });
