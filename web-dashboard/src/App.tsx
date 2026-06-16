import { useEffect, useState } from "react";
import { loadData } from "./loadData";
import type { DashboardData } from "./types";
import { Kpis } from "./components/Kpis";
import { GrowthChart } from "./components/GrowthChart";
import { CategoryBars } from "./components/CategoryBars";
import { FactsTable } from "./components/FactsTable";
import { Observations } from "./components/Observations";
import { EvolutionPanel } from "./components/EvolutionPanel";

export function App() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    loadData().then(setData);
  }, []);

  if (!data) {
    return <div className="loading">Loading dashboard…</div>;
  }

  const live = data.source === "live";
  const nodes = data.graph?.total_nodes ?? data.kpis.total_facts + data.kpis.total_observations;
  const connections =
    data.graph?.connections ?? data.kpis.total_facts * 2 + data.kpis.total_observations;
  const categories = data.graph?.categories ?? data.categories;

  return (
    <div className="wrap">
      <header className="page">
        <h1>
          SakThai <span>— Memory Dashboard</span>
        </h1>
        <span className="source-pill">
          <span className={live ? "dot live" : "dot demo"} />
          {live ? "live" : "demo"} · {data.generated_at}
        </span>
      </header>

      <Kpis kpis={data.kpis} nodes={nodes} connections={connections} />

      <div className="grid-2">
        <GrowthChart growth={data.growth} />
        <CategoryBars categories={categories} />
      </div>

      <div className="grid-2">
        <FactsTable facts={data.recent_facts} categories={categories} />
        <Observations observations={data.top_observations} />
      </div>

      {data.evolution && (
        <div style={{ marginTop: 8 }}>
          <EvolutionPanel evolution={data.evolution} />
        </div>
      )}

      <footer className="page">
        Static snapshot from{" "}
        <code>sakthai dashboard --export web-dashboard/public/data.json</code> ·{" "}
        <a href="https://github.com/beer-sakthai/sakthai-agent-v2">sakthai-agent-v2</a>
      </footer>
    </div>
  );
}
