"use client";

import { AlertTriangle, CheckCircle2, FlaskConical, HelpCircle } from "lucide-react";
import { DataSource } from "@/lib/types";

interface DataSourceBadgeProps {
  source?: DataSource;
  /** What the badge is describing, e.g. "eval.jsonl". Shown in the tooltip. */
  label?: string;
  className?: string;
}

const STYLES: Record<
  DataSource,
  { text: string; className: string; icon: typeof CheckCircle2; title: string }
> = {
  live: {
    text: "Live",
    className: "bg-emerald-950/50 text-emerald-300 border-emerald-800/50",
    icon: CheckCircle2,
    title: "Read from the agent's real files on this machine.",
  },
  demo: {
    text: "Demo",
    className: "bg-amber-950/50 text-amber-300 border-amber-800/50",
    icon: FlaskConical,
    title: "Sample data — not measured. Nothing here reflects real activity.",
  },
  unavailable: {
    text: "No data",
    className: "bg-rose-950/50 text-rose-300 border-rose-800/50",
    icon: AlertTriangle,
    title:
      "The source file does not exist on this machine, so sample data is shown in its place.",
  },
};

/**
 * Says where a panel's numbers came from.
 *
 * This is load-bearing rather than decorative. The data layer falls back to
 * demo data whenever a source is missing or unreadable, so without this badge a
 * machine with no ~/.sakthai renders a fully populated dashboard that is
 * indistinguishable from a busy one.
 */
export function DataSourceBadge({ source, label, className = "" }: DataSourceBadgeProps) {
  if (!source) return null;
  const style = STYLES[source];
  if (!style) return null;
  const Icon = style.icon ?? HelpCircle;

  return (
    <span
      data-testid="data-source-badge"
      data-source={source}
      title={label ? `${label} — ${style.title}` : style.title}
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide ${style.className} ${className}`}
    >
      <Icon className="h-3 w-3" aria-hidden="true" />
      {style.text}
      {label && <span className="text-[9px] opacity-70">· {label}</span>}
    </span>
  );
}

export default DataSourceBadge;
