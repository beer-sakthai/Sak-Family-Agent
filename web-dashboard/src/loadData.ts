import type { DashboardData } from "./types";

// Built-in fallback so the page renders even when data.json is missing or
// unreachable (e.g. opened via file://). Mirrors the demo sample in
// sakthai/dashboard/data.py.
export const DEMO: DashboardData = {
  generated_at: "demo",
  source: "demo",
  kpis: {
    total_facts: 5,
    total_facts_delta: 5,
    total_observations: 2,
    total_observations_delta: 2,
  },
  growth: {
    labels: ["1", "2", "3", "4", "5", "6", "7"],
    facts: [1, 2, 2, 3, 4, 4, 5],
    observations: [0, 0, 1, 1, 1, 2, 2],
  },
  recent_facts: [
    { id: 5, kind: "pref", key: "language", value: "Python" },
    { id: 4, kind: "pref", key: "editor", value: "VS Code" },
    { id: 3, kind: "profile", key: "timezone", value: "Asia/Bangkok" },
    { id: 2, kind: "note", key: "", value: "Prefers concise replies" },
    { id: 1, kind: "project", key: "", value: "Building SakThai" },
  ],
  top_observations: [
    { summary: "Prefers Python for data tasks", weight: 0.95 },
    { summary: "Most active in the evening", weight: 0.8 },
  ],
  categories: [
    { name: "Pref", count: 2, color: "#a855f7" },
    { name: "Profile", count: 1, color: "#34d399" },
    { name: "Note", count: 1, color: "#3b82f6" },
    { name: "Project", count: 1, color: "#22d3ee" },
    { name: "Observations", count: 2, color: "#f472b6" },
  ],
};

export async function loadData(): Promise<DashboardData> {
  // BASE_URL is the Vite `base` (e.g. /sakthai-agent-v2/), so the fetch resolves
  // correctly whether served from a project sub-path or the domain root.
  const url = `${import.meta.env.BASE_URL}data.json`;
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = (await res.json()) as DashboardData;
    // Guard against a truncated/garbage file.
    if (!data || !data.kpis || !data.growth) throw new Error("malformed snapshot");
    return data;
  } catch {
    return DEMO;
  }
}
