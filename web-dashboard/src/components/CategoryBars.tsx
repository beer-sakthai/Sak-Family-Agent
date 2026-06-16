import type { Category } from "../types";

export function CategoryBars({ categories }: { categories: Category[] }) {
  const max = Math.max(1, ...categories.map((c) => c.count));
  return (
    <div className="card">
      <h2 className="card-title">By category</h2>
      {categories.length === 0 ? (
        <p className="empty">No categories yet.</p>
      ) : (
        <div className="bars">
          {categories.map((c) => (
            <div className="bar-row" key={c.name}>
              <span>{c.name}</span>
              <span className="bar-track">
                <span
                  className="bar-fill"
                  style={{ width: `${(c.count / max) * 100}%`, background: c.color }}
                />
              </span>
              <span className="bar-count">{c.count}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
