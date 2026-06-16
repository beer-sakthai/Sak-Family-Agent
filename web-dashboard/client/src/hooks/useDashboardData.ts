import { useEffect, useState } from "react";

export interface KPIs {
  total_facts: number;
  total_facts_delta: number;
  total_observations: number;
  total_observations_delta: number;
}

export interface GrowthData {
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
  id: number;
  kind: string;
  key?: string;
  value: string;
  created?: string;
}

export interface Observation {
  summary: string;
  weight: number;
}

export interface DashboardData {
  generated_at: string;
  source: "live" | "demo";
  kpis: KPIs;
  growth: GrowthData;
  categories: Category[];
  recent_facts: Fact[];
  top_observations: Observation[];
}

const DEMO_DATA: DashboardData = {
  generated_at: new Date().toISOString(),
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
  categories: [
    { name: "Pref", count: 2, color: "#a855f7" },
    { name: "Profile", count: 1, color: "#34d399" },
    { name: "Note", count: 1, color: "#3b82f6" },
    { name: "Observations", count: 2, color: "#f472b6" },
  ],
  recent_facts: [
    { id: 5, kind: "pref", key: "language", value: "Python" },
    { id: 4, kind: "pref", key: "editor", value: "VS Code" },
  ],
  top_observations: [{ summary: "Prefers concise replies", weight: 0.9 }],
};

export function useDashboardData() {
  const [data, setData] = useState<DashboardData>(DEMO_DATA);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch("/data.json");
        if (response.ok) {
          const json = await response.json();
          setData(json);
          setError(null);
        } else {
          setData(DEMO_DATA);
        }
      } catch (err) {
        setData(DEMO_DATA);
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}
