import { Brain } from "lucide-react";

interface DashboardHeaderProps {
  source: "live" | "demo";
  generatedAt: string;
}

export function DashboardHeader({ source, generatedAt }: DashboardHeaderProps) {
  const isLive = source === "live";
  const date = new Date(generatedAt).toLocaleString();

  return (
    <div className="border-b border-slate-700/50 bg-gradient-to-b from-slate-900/50 to-transparent">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 flex items-center justify-center">
            <Brain className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold font-mono glow-accent">SakThai</h1>
            <p className="text-sm text-slate-400 font-mono">Agent Memory Dashboard</p>
          </div>
        </div>
        <div className="flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isLive ? "bg-emerald-500 animate-pulse" : "bg-slate-600"
              }`}
            />
            <span>{isLive ? "Live Data" : "Demo Data"}</span>
          </div>
          <span>Generated: {date}</span>
        </div>
      </div>
    </div>
  );
}
