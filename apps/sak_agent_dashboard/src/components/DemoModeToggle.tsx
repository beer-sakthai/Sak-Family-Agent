"use client";

import React from "react";
import { Cloud, Database, FlaskConical } from "lucide-react";

import type { DataSource } from "@/lib/contracts.generated";

interface DemoModeToggleProps {
  isDemo: boolean;
  onToggle: (isDemo: boolean) => void;
  /** What the last response actually came from — not what was requested. */
  activeSource: DataSource | null;
}

const SOURCE_LABELS: Record<
  DataSource,
  { label: string; title: string; icon: React.ReactNode; classes: string }
> = {
  local: {
    label: "Live · local ~/.sakthai",
    title: "Data source: Local runtime directory (~/.sakthai)",
    icon: <Database className="h-3 w-3" aria-hidden />,
    classes: "bg-hue-emerald/10 text-hue-emerald border-hue-emerald-line/30",
  },
  api: {
    label: "Live · SakThai API",
    title: "Data source: Remote SakThai API endpoint",
    icon: <Cloud className="h-3 w-3" aria-hidden />,
    classes: "bg-hue-cyan/10 text-hue-cyan border-hue-cyan-line/30",
  },
  demo: {
    label: "Sample data",
    title: "Data source: Demonstration sample dataset",
    icon: <FlaskConical className="h-3 w-3" aria-hidden />,
    classes: "bg-hue-amber/10 text-hue-amber border-hue-amber-line/30",
  },
};

export function DemoModeToggle({ isDemo, onToggle, activeSource }: DemoModeToggleProps) {
  const source = activeSource ? SOURCE_LABELS[activeSource] : null;

  return (
    <div className="flex items-center gap-2">
      {/* The source badge reports what the data actually is. It can disagree
          with the toggle -- asking for live data on a host with no
          ~/.sakthai falls back to demo, and this is how you find out. */}
      {source && (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono border ${source.classes}`}
          data-testid="active-source"
          title={source.title}
          aria-label={source.title}
        >
          {source.icon}
          {source.label}
        </span>
      )}

      <button
        onClick={() => onToggle(!isDemo)}
        aria-pressed={isDemo}
        aria-label="Toggle sample data"
        title={isDemo ? "Switch to live agent data" : "Switch to sample dataset"}
        className={`px-3 py-1.5 rounded-xl text-[11px] font-mono border transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
          isDemo
            ? "bg-hue-amber-tint/40 text-hue-amber border-hue-amber-line/50"
            : "bg-panel/60 text-fg-3 border-line hover:border-line-strong"
        }`}
      >
        {/* "Sample" not "Sample data": the badge to its left already reads
            "Sample data" whenever that is what is being served, and two
            controls a centimetre apart saying the same words is a puzzle. */}
        Sample: {isDemo ? "ON" : "OFF"}
      </button>
    </div>
  );
}

export default DemoModeToggle;
