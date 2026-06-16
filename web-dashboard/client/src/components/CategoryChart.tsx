import type { Category } from "@/hooks/useDashboardData";
import { Card } from "@/components/ui/card";
import { Layers } from "lucide-react";

interface CategoryChartProps {
  categories: Category[];
}

export function CategoryChart({ categories }: CategoryChartProps) {
  const maxCount = Math.max(1, ...categories.map((c) => c.count));
  const totalCount = categories.reduce((sum, c) => sum + c.count, 0);

  return (
    <Card className="p-6 border-cyan-500/30 bg-slate-900/50">
      <div className="mb-4">
        <h2 className="text-xl font-bold font-mono glow-accent mb-1 flex items-center gap-2">
          <Layers className="w-5 h-5" />
          By Category
        </h2>
        <p className="text-xs text-slate-500">Distribution of facts by type</p>
      </div>
      <div className="space-y-4">
        {categories.map((category) => {
          const percentage = ((category.count / totalCount) * 100).toFixed(1);
          return (
            <div key={category.name} className="group">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-300">{category.name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-400">{percentage}%</span>
                  <span className="text-sm font-mono font-bold" style={{ color: category.color }}>
                    {category.count}
                  </span>
                </div>
              </div>
              <div className="flex-1 bg-slate-800/50 rounded-lg h-7 overflow-hidden border border-slate-700/40 group-hover:border-slate-600/60 transition-all duration-200">
                <div
                  className="h-full transition-all duration-700 ease-out relative overflow-hidden"
                  style={{
                    width: `${(category.count / maxCount) * 100}%`,
                    backgroundColor: category.color,
                    boxShadow: `0 0 16px ${category.color}50`,
                  }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {categories.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-700/30 text-xs text-slate-500 text-center">
          Total: {totalCount} item{totalCount !== 1 ? "s" : ""} across {categories.length} categor{categories.length !== 1 ? "ies" : "y"}
        </div>
      )}
    </Card>
  );
}
