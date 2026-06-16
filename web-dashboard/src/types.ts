// Shape of the snapshot produced by `sakthai dashboard --export web-dashboard/public/data.json`
// (see sakthai/dashboard/data.py :: collect_dashboard_data). The richer fields —
// `graph`, `evolution`, `chat` — are optional so the app renders against both the
// minimal and the extended export.

export interface Kpis {
  total_facts: number;
  total_facts_delta: number;
  total_observations: number;
  total_observations_delta: number;
}

export interface Growth {
  labels: string[];
  facts: number[];
  observations: number[];
}

export interface Category {
  name: string;
  count: number;
  color: string;
}

export interface Fact {
  id?: number;
  kind: string;
  key?: string;
  value: string;
  created?: string;
}

export interface Observation {
  summary: string;
  weight: number;
}

export interface EvolutionEntry {
  version: string;
  date: string;
  success: number;
  gain?: string;
  latest?: boolean;
}

export interface Evolution {
  current_version: string;
  performance_gain: string;
  runs: number;
  success_rate: number;
  history: EvolutionEntry[];
  before_after: { accuracy: { before: number; after: number } };
  neural_focus: { name: string; pct: number }[];
}

export interface DashboardData {
  generated_at: string;
  source: "live" | "demo" | string;
  kpis: Kpis;
  growth: Growth;
  recent_facts: Fact[];
  top_observations: Observation[];
  categories: Category[];
  graph?: { categories: Category[]; total_nodes: number; connections: number };
  evolution?: Evolution;
}
