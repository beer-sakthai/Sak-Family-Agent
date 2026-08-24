"use client";

import React from "react";
import { Sparkles, Database } from "lucide-react";

interface DemoModeToggleProps {
  isDemo: boolean;
  onToggle: (val?: boolean) => void;
}

export function DemoModeToggle({ isDemo, onToggle }: DemoModeToggleProps) {
  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        aria-pressed={isDemo}
        aria-label={`Toggle Demo Mode, currently ${isDemo ? "ON" : "OFF"}`}
        onClick={() => onToggle(!isDemo)}
        className={`relative inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold font-mono transition-all duration-300 border shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-950 ${
          isDemo
            ? "bg-purple-950/60 border-purple-500/40 text-purple-300 shadow-purple-900/30 hover:bg-purple-900/60"
            : "bg-slate-900/80 border-slate-700/80 text-slate-300 shadow-slate-950 hover:bg-slate-800/80"
        }`}
      >
        <span
          className={`h-2 w-2 rounded-full transition-all duration-300 ${
            isDemo
              ? "bg-purple-400 animate-pulse shadow-[0_0_8px_rgba(192,132,252,0.8)]"
              : "bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]"
          }`}
        />
        {isDemo ? (
          <span className="flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-purple-400" />
            Demo Mode: ON
          </span>
        ) : (
          <span className="flex items-center gap-1.5">
            <Database className="h-3.5 w-3.5 text-cyan-400" />
            Demo Mode: OFF (Real ~/.sakthai Data)
          </span>
        )}
      </button>

      <span
        className={`text-[10px] uppercase font-mono font-bold px-2 py-0.5 rounded-full border ${
          isDemo
            ? "bg-purple-500/10 text-purple-400 border-purple-500/30"
            : "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
        }`}
      >
        {isDemo ? "Sample Data" : "Live Runtime"}
      </span>
    </div>
  );
}

export default DemoModeToggle;
