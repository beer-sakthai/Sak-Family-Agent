import type { Category, Fact } from "../types";

const FALLBACK = "#3b82f6";

export function FactsTable({ facts, categories }: { facts: Fact[]; categories: Category[] }) {
  // Tint each kind's pill with its category colour where available.
  const colorByKind = new Map(categories.map((c) => [c.name.toLowerCase(), c.color]));

  return (
    <div className="card">
      <h2 className="card-title">Recent facts</h2>
      {facts.length === 0 ? (
        <p className="empty">No facts yet — run `sakthai learn "..."`.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Kind</th>
              <th>Key</th>
              <th>Value</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {facts.map((f, i) => {
              const color = colorByKind.get(f.kind.toLowerCase()) ?? FALLBACK;
              return (
                <tr key={f.id ?? i}>
                  <td className="kind">
                    <span className="tag" style={{ color, borderColor: color }}>
                      {f.kind}
                    </span>
                  </td>
                  <td>{f.key || "—"}</td>
                  <td>{f.value}</td>
                  <td>{f.created || "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
