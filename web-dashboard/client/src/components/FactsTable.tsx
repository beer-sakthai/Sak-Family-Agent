import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { Fact } from "@/hooks/useDashboardData";
import { Calendar, Tag } from "lucide-react";

interface FactsTableProps {
  facts: Fact[];
}

const kindColors: Record<string, string> = {
  pref: "bg-purple-500/20 text-purple-300 border border-purple-500/30",
  preference: "bg-purple-500/20 text-purple-300 border border-purple-500/30",
  profile: "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30",
  note: "bg-blue-500/20 text-blue-300 border border-blue-500/30",
  project: "bg-amber-500/20 text-amber-300 border border-amber-500/30",
  skill: "bg-orange-500/20 text-orange-300 border border-orange-500/30",
  decision: "bg-pink-500/20 text-pink-300 border border-pink-500/30",
  lesson: "bg-orange-500/20 text-orange-300 border border-orange-500/30",
  fact: "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30",
};

export function FactsTable({ facts }: FactsTableProps) {
  return (
    <Card className="p-6 border-cyan-500/30 bg-slate-900/50">
      <div className="mb-4">
        <h2 className="text-xl font-bold font-mono glow-accent mb-1 flex items-center gap-2">
          <Tag className="w-5 h-5" />
          Recent Facts
        </h2>
        <p className="text-xs text-slate-500">Latest recorded facts and preferences</p>
      </div>
      <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
        {facts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Tag className="w-8 h-8 text-slate-600 mb-2 opacity-50" />
            <p className="text-sm text-slate-500">No facts recorded yet</p>
            <p className="text-xs text-slate-600 mt-1">Facts will appear here as they are learned</p>
          </div>
        ) : (
          facts.map((fact) => (
            <div
              key={fact.id}
              className="group flex items-start gap-3 p-4 rounded-lg bg-slate-800/30 border border-slate-700/40 hover:border-cyan-500/50 hover:bg-slate-800/50 transition-all duration-200"
            >
              <Badge
                className={`${kindColors[fact.kind] || "bg-slate-500/20 text-slate-300 border border-slate-500/30"} flex-shrink-0 text-xs font-semibold`}
              >
                {fact.kind}
              </Badge>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-200 font-medium">
                  {fact.key ? (
                    <>
                      <span className="text-cyan-400 font-mono text-xs mr-1">{fact.key}</span>
                      <span className="text-slate-400">→</span>
                      <span className="ml-1">{fact.value}</span>
                    </>
                  ) : (
                    fact.value
                  )}
                </p>
                {fact.created && (
                  <div className="flex items-center gap-1 text-xs text-slate-500 mt-2">
                    <Calendar className="w-3 h-3" />
                    <span>{fact.created}</span>
                  </div>
                )}
              </div>
              <div className="text-xs text-slate-600 group-hover:text-slate-500 transition-colors flex-shrink-0">#{fact.id}</div>
            </div>
          ))
        )}
      </div>
      {facts.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-700/30 text-xs text-slate-500 text-center">
          Showing {facts.length} recent fact{facts.length !== 1 ? "s" : ""}
        </div>
      )}
    </Card>
  );
}
