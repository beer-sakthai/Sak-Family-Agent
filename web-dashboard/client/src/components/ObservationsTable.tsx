import type { Observation } from "@/hooks/useDashboardData";

interface ObservationsTableProps {
  observations: Observation[];
}

export function ObservationsTable({ observations }: ObservationsTableProps) {
  return (
    <div className="glow-card p-6">
      <h2 className="text-lg font-semibold font-mono glow-text mb-4">Top Observations</h2>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {observations.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-8">No observations yet</p>
        ) : (
          observations.map((obs, idx) => (
            <div
              key={idx}
              className="flex items-start gap-3 p-3 rounded bg-slate-800/30 border border-slate-700/30 hover:border-magenta-500/30 transition-colors"
            >
              <div className="flex-shrink-0 w-12 h-12 rounded bg-gradient-to-br from-magenta-500/20 to-purple-500/20 border border-magenta-500/30 flex items-center justify-center">
                <span className="text-sm font-mono font-bold text-magenta-400">
                  {(obs.weight * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex-1">
                <p className="text-sm text-slate-300">{obs.summary}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
