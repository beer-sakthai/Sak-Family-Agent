import type { Category } from "@/hooks/useDashboardData";

interface CategoryChartProps {
  categories: Category[];
}

export function CategoryChart({ categories }: CategoryChartProps) {
  const maxCount = Math.max(1, ...categories.map((c) => c.count));

  return (
    <div className="glow-card p-6">
      <h2 className="text-lg font-semibold font-mono glow-text mb-4">By Category</h2>
      <div className="space-y-4">
        {categories.map((category) => (
          <div key={category.name} className="flex items-center gap-3">
            <span className="text-sm font-medium text-slate-400 min-w-24">{category.name}</span>
            <div className="flex-1 bg-slate-800/50 rounded h-6 overflow-hidden border border-slate-700/50">
              <div
                className="h-full transition-all duration-500 ease-out"
                style={{
                  width: `${(category.count / maxCount) * 100}%`,
                  backgroundColor: category.color,
                  boxShadow: `0 0 12px ${category.color}40`,
                }}
              />
            </div>
            <span className="text-sm font-mono text-cyan-400 min-w-8 text-right">{category.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
