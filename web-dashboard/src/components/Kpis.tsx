import type { Kpis as KpisType } from "../types";

function Kpi({ label, value, delta }: { label: string; value: number; delta: number }) {
  return (
    <div className="card kpi">
      <div className="label">{label}</div>
      <div className="value">{value.toLocaleString()}</div>
      <div className={delta > 0 ? "delta" : "delta flat"}>
        {delta > 0 ? `+${delta} this week` : "no change this week"}
      </div>
    </div>
  );
}

export function Kpis({ kpis, nodes, connections }: { kpis: KpisType; nodes: number; connections: number }) {
  return (
    <section className="kpis">
      <Kpi label="Total Facts" value={kpis.total_facts} delta={kpis.total_facts_delta} />
      <Kpi
        label="Observations"
        value={kpis.total_observations}
        delta={kpis.total_observations_delta}
      />
      <div className="card kpi">
        <div className="label">Knowledge Nodes</div>
        <div className="value">{nodes.toLocaleString()}</div>
        <div className="delta flat">facts + observations</div>
      </div>
      <div className="card kpi">
        <div className="label">Connections</div>
        <div className="value">{connections.toLocaleString()}</div>
        <div className="delta flat">graph edges</div>
      </div>
    </section>
  );
}
