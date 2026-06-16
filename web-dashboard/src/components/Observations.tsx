import type { Observation } from "../types";

export function Observations({ observations }: { observations: Observation[] }) {
  return (
    <div className="card">
      <h2 className="card-title">Top observations</h2>
      {observations.length === 0 ? (
        <p className="empty">No observations yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Observation</th>
              <th>Weight</th>
            </tr>
          </thead>
          <tbody>
            {observations.map((o, i) => (
              <tr key={i}>
                <td>{o.summary}</td>
                <td>{o.weight.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
