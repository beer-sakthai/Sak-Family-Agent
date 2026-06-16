import type { Evolution } from "../types";

// Rendered only when the snapshot includes an `evolution` block (the extended
// export). Shows headline metrics, version history, and before/after accuracy.
export function EvolutionPanel({ evolution }: { evolution: Evolution }) {
  const { before, after } = evolution.before_after.accuracy;
  return (
    <div className="card">
      <h2 className="card-title">Evolution</h2>
      <section className="kpis" style={{ marginBottom: 18 }}>
        <div className="kpi">
          <div className="label">Version</div>
          <div className="value" style={{ fontSize: "1.6rem" }}>
            {evolution.current_version}
          </div>
        </div>
        <div className="kpi">
          <div className="label">Gain</div>
          <div className="value" style={{ fontSize: "1.6rem" }}>
            {evolution.performance_gain}
          </div>
        </div>
        <div className="kpi">
          <div className="label">Runs</div>
          <div className="value" style={{ fontSize: "1.6rem" }}>
            {evolution.runs}
          </div>
        </div>
        <div className="kpi">
          <div className="label">Success</div>
          <div className="value" style={{ fontSize: "1.6rem" }}>
            {evolution.success_rate}%
          </div>
        </div>
      </section>

      <div className="bars" style={{ marginBottom: 18 }}>
        <div className="bar-row">
          <span>Accuracy before</span>
          <span className="bar-track">
            <span className="bar-fill" style={{ width: `${before}%`, background: "#3b2b5a" }} />
          </span>
          <span className="bar-count">{before}%</span>
        </div>
        <div className="bar-row">
          <span>Accuracy after</span>
          <span className="bar-track">
            <span className="bar-fill" style={{ width: `${after}%`, background: "#3b82f6" }} />
          </span>
          <span className="bar-count">{after}%</span>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Version</th>
            <th>Date</th>
            <th>Success</th>
          </tr>
        </thead>
        <tbody>
          {evolution.history.map((h) => (
            <tr key={h.version}>
              <td>
                {h.latest ? (
                  <span className="tag" style={{ color: "#d8b4fe", borderColor: "#a855f7" }}>
                    {h.version} · latest
                  </span>
                ) : (
                  h.version
                )}
              </td>
              <td>{h.date}</td>
              <td>{h.success}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
