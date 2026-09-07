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

const SOURCE_LABELS: Record<DataSource, { label: string; icon: React.ReactNode; classes: string }> =
  {
    local: {
      label: "Live · local ~/.sakthai",
      icon: <Database className="h-3 w-3" aria-hidden />,
      classes: "bg-hue-emerald/10 text-hue-emerald border-hue-emerald-line/30",
    },
    api: {
      label: "Live · SakThai API",
      icon: <Cloud className="h-3 w-3" aria-hidden />,
      classes: "bg-hue-cyan/10 text-hue-cyan border-hue-cyan-line/30",
    },
    demo: {
      label: "Sample data",
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
        >
          {source.icon}
          {source.label}
        </span>
      )}

      <button
        onClick={() => onToggle(!isDemo)}
        aria-pressed={isDemo}
        aria-label="Toggle sample data"
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
