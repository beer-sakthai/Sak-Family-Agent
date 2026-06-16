import { Badge } from "@/components/ui/badge";
import type { Fact } from "@/hooks/useDashboardData";

interface FactsTableProps {
  facts: Fact[];
}

const kindColors: Record<string, string> = {
  pref: "bg-purple-500/20 text-purple-300",
  profile: "bg-emerald-500/20 text-emerald-300",
  note: "bg-blue-500/20 text-blue-300",
  observation: "bg-pink-500/20 text-pink-300",
};

export function FactsTable({ facts }: FactsTableProps) {
  return (
    <div className="glow-card p-6">
      <h2 className="text-lg font-semibold font-mono glow-text mb-4">Recent Facts</h2>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {facts.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-8">No facts recorded yet</p>
        ) : (
          facts.map((fact) => (
            <div
              key={fact.id}
              className="flex items-start gap-3 p-3 rounded bg-slate-800/30 border border-slate-700/30 hover:border-cyan-500/30 transition-colors"
            >
              <Badge className={`${kindColors[fact.kind] || "bg-slate-500/20 text-slate-300"} flex-shrink-0`}>
                {fact.kind}
              </Badge>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-300">
                  {fact.key ? (
                    <>
                      <span className="text-cyan-400 font-mono">{fact.key}:</span> {fact.value}
                    </>
                  ) : (
                    fact.value
                  )}
                </p>
                {fact.created && <p className="text-xs text-slate-500 mt-1">{fact.created}</p>}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
