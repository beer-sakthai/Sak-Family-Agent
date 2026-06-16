import { Brain, Moon, Sun } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";

interface DashboardHeaderProps {
  source: "live" | "demo";
  generatedAt: string;
}

export function DashboardHeader({ source, generatedAt }: DashboardHeaderProps) {
  const isLive = source === "live";
  const date = new Date(generatedAt);
  const formattedDate = date.toLocaleString();
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="border-b border-cyan-500/20 bg-gradient-to-b from-slate-900/80 to-slate-950/50 backdrop-blur-sm">
      {/* Geometric top accent line */}
      <div className="h-0.5 bg-gradient-to-r from-cyan-500/0 via-cyan-500/50 to-cyan-500/0" />
      
      <div className="container mx-auto px-4 py-6">
        {/* Header Top Section */}
        <div className="flex items-center justify-between mb-6">
          {/* Logo & Title */}
          <div className="flex items-center gap-4">
            <div className="relative w-14 h-14 rounded-lg bg-gradient-to-br from-cyan-500/30 to-purple-500/20 border border-cyan-500/40 flex items-center justify-center group hover:border-cyan-500/60 transition-colors duration-200">
              <Brain className="w-7 h-7 text-cyan-400 group-hover:drop-shadow-lg group-hover:drop-shadow-cyan-500/50 transition-all duration-200" />
              {/* Glow effect on hover */}
              <div className="absolute inset-0 rounded-lg bg-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-200 blur-lg" />
            </div>
            <div>
              <h1 className="text-4xl font-bold font-mono glow-accent tracking-tighter">SakThai</h1>
              <p className="text-sm text-slate-400 font-mono tracking-wide">Agent Memory Dashboard</p>
            </div>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg border border-slate-600/50 bg-slate-800/50 hover:bg-slate-700/50 hover:border-cyan-500/50 transition-all duration-200 text-slate-400 hover:text-cyan-400"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? (
              <Sun className="w-5 h-5" />
            ) : (
              <Moon className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Header Bottom Section - Status & Metadata */}
        <div className="flex items-center justify-between text-xs">
          {/* Left: Live Status */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-800/50 border border-slate-700/50">
              <div
                className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                  isLive
                    ? "bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse"
                    : "bg-slate-600"
                }`}
              />
              <span className="font-mono text-slate-300 font-medium">
                {isLive ? "Live Data" : "Demo Data"}
              </span>
            </div>

            {/* Data Source Indicator */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-800/50 border border-slate-700/50 text-slate-400">
              <span className="text-xs uppercase tracking-wide">Source:</span>
              <span className="font-mono text-cyan-400">{source}</span>
            </div>
          </div>

          {/* Right: Timestamp & Timezone */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-800/50 border border-slate-700/50">
            <span className="text-slate-400 font-mono">
              Generated: <span className="text-cyan-400">{formattedDate}</span>
            </span>
            <span className="hidden sm:inline text-slate-500 text-xs">({timezone})</span>
          </div>
        </div>
      </div>

      {/* Geometric bottom accent line */}
      <div className="h-0.5 bg-gradient-to-r from-purple-500/0 via-purple-500/30 to-purple-500/0" />
    </div>
  );
}
