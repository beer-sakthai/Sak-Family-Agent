import type { Observation } from "@/hooks/useDashboardData";
import { Card } from "@/components/ui/card";
import { Lightbulb } from "lucide-react";

interface ObservationsTableProps {
  observations: Observation[];
}

export function ObservationsTable({ observations }: ObservationsTableProps) {
  const getConfidenceColor = (weight: number) => {
    if (weight >= 0.8) return "from-emerald-500/30 to-emerald-600/20 border-emerald-500/40 text-emerald-300";
    if (weight >= 0.6) return "from-cyan-500/30 to-cyan-600/20 border-cyan-500/40 text-cyan-300";
    if (weight >= 0.4) return "from-amber-500/30 to-amber-600/20 border-amber-500/40 text-amber-300";
    return "from-slate-500/30 to-slate-600/20 border-slate-500/40 text-slate-300";
  };

  return (
    <Card className="p-6 border-purple-500/30 bg-slate-900/50">
      <div className="mb-4">
        <h2 className="text-xl font-bold font-mono glow-accent mb-1 flex items-center gap-2">
          <Lightbulb className="w-5 h-5" />
          Top Observations
        </h2>
        <p className="text-xs text-slate-500">Learned patterns and insights</p>
      </div>
      <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
        {observations.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Lightbulb className="w-8 h-8 text-slate-600 mb-2 opacity-50" />
            <p className="text-sm text-slate-500">No observations yet</p>
            <p className="text-xs text-slate-600 mt-1">Patterns will appear as the agent learns</p>
          </div>
        ) : (
          observations.map((obs, idx) => {
            const confidence = obs.weight * 100;
            const colorClass = getConfidenceColor(obs.weight);
            return (
              <div
                key={idx}
                className="group flex items-start gap-4 p-4 rounded-lg bg-slate-800/30 border border-slate-700/40 hover:border-purple-500/50 hover:bg-slate-800/50 transition-all duration-200"
              >
                <div
                  className={`flex-shrink-0 w-14 h-14 rounded-lg bg-gradient-to-br ${colorClass} border flex items-center justify-center`}
                >
                  <div className="flex flex-col items-center">
                    <span className="text-lg font-mono font-bold">{confidence.toFixed(0)}%</span>
                    <span className="text-xs text-slate-400 font-medium">confidence</span>
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200 font-medium leading-relaxed">{obs.summary}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <div className="h-1 flex-1 bg-slate-700/50 rounded-full overflow-hidden">
                      <div
                        className={`h-full bg-gradient-to-r ${confidence >= 0.8 ? "from-emerald-500 to-emerald-600" : confidence >= 0.6 ? "from-cyan-500 to-cyan-600" : confidence >= 0.4 ? "from-amber-500 to-amber-600" : "from-slate-500 to-slate-600"}`}
                        style={{ width: `${confidence}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
      {observations.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-700/30 text-xs text-slate-500 text-center">
          {observations.length} observation{observations.length !== 1 ? "s" : ""} · Avg confidence: {(observations.reduce((sum, o) => sum + o.weight, 0) / observations.length * 100).toFixed(0)}%
        </div>
      )}
    </Card>
  );
}
