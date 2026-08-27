"use client";

import React from "react";
import {
  Activity,
  AlertTriangle,
  Brain,
  Clock,
  Database,
  MessageSquare,
  TrendingDown,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

import type {
  AuditPayload,
  MemoryPayload,
  MetricsPayload,
  SessionsPayload,
} from "@/lib/contracts.generated";
import { compactNumber, duration, percent } from "@/lib/format";
import type { TabId } from "@/lib/nav";

interface KpiStripProps {
  metrics: MetricsPayload | null;
  memory: MemoryPayload | null;
  sessions: SessionsPayload | null;
  audit: AuditPayload | null;
  /** When given, a tile becomes a shortcut to the panel behind its figure. */
  onNavigate?: (tab: TabId) => void;
}

interface Tile {
  label: string;
  value: string;
  hint: string;
  icon: LucideIcon;
  accent: string;
  /** Percentage points of change, when a comparable prior period exists. */
  delta?: { value: number; goodWhenUp: boolean } | null;
  /** Normalised 0..1 series drawn as a sparkline behind the figure. */
  series?: number[];
  /** The panel this figure is drawn from, when there is one to jump to. */
  tab?: TabId;
}

/**
 * A sparkline as a single inline `<svg>` path.
 *
 * Deliberately not Recharts: these are decoration at 40px tall, six of them on
 * screen at once, and a ResponsiveContainer each would cost a measurement pass
 * apiece for a line nobody hovers.
 */
function Sparkline({ values, className }: { values: number[]; className: string }) {
  if (values.length < 2) return null;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const span = max - min || 1;
  const step = 100 / (values.length - 1);
  const points = values
    .map((value, index) => `${(index * step).toFixed(2)},${(28 - ((value - min) / span) * 24).toFixed(2)}`)
    .join(" ");

  return (
    <svg
      viewBox="0 0 100 28"
      preserveAspectRatio="none"
      aria-hidden
      className={`absolute inset-x-0 bottom-0 h-7 w-full opacity-30 ${className}`}
    >
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

function TileCard({ tile, onNavigate }: { tile: Tile; onNavigate?: (tab: TabId) => void }) {
  const Icon = tile.icon;
  const delta = tile.delta;
  const deltaGood = delta ? (delta.value >= 0) === delta.goodWhenUp : false;

  // A figure that comes from a panel should get you to that panel. Tiles with
  // no panel behind them (success rate, latency — both aggregates over the
  // eval log rather than a view) stay inert rather than becoming buttons that
  // navigate somewhere arbitrary.
  const target = tile.tab;
  const Root = target && onNavigate ? "button" : "div";
  const interactive =
    target && onNavigate
      ? {
          type: "button" as const,
          onClick: () => onNavigate(target),
          "aria-label": `${tile.label}: ${tile.value}. Open the ${target} panel.`,
        }
      : {};

  return (
    // pb-9 reserves the strip the sparkline occupies, so the line sits under
    // the figure rather than striking through the hint beneath it.
    <Root
      {...interactive}
      className={`group relative w-full overflow-hidden rounded-2xl border border-line/80 bg-panel/70 p-4 pb-9 text-left backdrop-blur-xl transition-colors hover:border-line-strong focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
        target && onNavigate ? "cursor-pointer hover:border-accent/40" : ""
      }`}
    >
      {tile.series && <Sparkline values={tile.series} className={tile.accent} />}
      <div className="relative flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-fg-4">
            <Icon className={`h-3 w-3 ${tile.accent}`} />
            {tile.label}
          </p>
          <p className="mt-1.5 font-display text-2xl font-bold tracking-tight text-fg">
            {tile.value}
          </p>
          <p className="mt-0.5 truncate font-mono text-[11px] text-fg-4">{tile.hint}</p>
        </div>
        {delta && Number.isFinite(delta.value) && delta.value !== 0 && (
          <span
            data-testid="kpi-delta"
            className={`inline-flex shrink-0 items-center gap-1 rounded-full border px-1.5 py-0.5 font-mono text-[10px] ${
              deltaGood
                ? "border-hue-emerald-line/50 bg-hue-emerald-tint/40 text-hue-emerald"
                : "border-hue-rose-line/50 bg-hue-rose-tint/40 text-hue-rose"
            }`}
          >
            {delta.value >= 0 ? (
              <TrendingUp className="h-2.5 w-2.5" />
            ) : (
              <TrendingDown className="h-2.5 w-2.5" />
            )}
            {Math.abs(delta.value).toFixed(0)}%
          </span>
        )}
      </div>
    </Root>
  );
}

/**
 * The headline figures, above every section.
 *
 * Each tile states what it is derived from. Where a figure cannot be computed
 * — no runs recorded, no audit log — it renders an em dash and says why in the
 * hint, rather than showing a zero that reads as a measurement.
 */
export function KpiStrip({ metrics, memory, sessions, audit, onNavigate }: KpiStripProps) {
  const trends = metrics?.trends ?? [];
  const runsSeries = trends.map((point) => point.runs);
  const latencySeries = trends.map((point) => point.avg_latency_ms);
  const tokenSeries = trends.map((point) => point.input_tokens + point.output_tokens);

  // Week over week, only when there are two full windows to compare. With
  // fewer points the honest answer is "no comparison", not a 0% delta.
  const runsDelta = (() => {
    if (trends.length < 4) return null;
    const half = Math.floor(trends.length / 2);
    const older = trends.slice(0, half).reduce((sum, point) => sum + point.runs, 0);
    const recent = trends.slice(half).reduce((sum, point) => sum + point.runs, 0);
    if (older === 0) return null;
    return { value: ((recent - older) / older) * 100, goodWhenUp: true };
  })();

  const totalRuns = metrics?.total_runs ?? 0;
  const successRate = metrics && totalRuns > 0 ? (1 - metrics.error_rate) * 100 : null;
  const errorCount = metrics ? Math.round(metrics.error_rate * totalRuns) : 0;
  const criticalEvents =
    (audit?.severity_counts.critical ?? 0) + (audit?.severity_counts.high ?? 0);

  const tiles: Tile[] = [
    {
      label: "Total runs",
      value: metrics ? totalRuns.toLocaleString() : "—",
      hint: metrics ? "from eval.jsonl" : "no metrics yet",
      icon: Activity,
      accent: "text-hue-cyan",
      delta: runsDelta,
      series: runsSeries,
      tab: "analytics",
    },
    {
      label: "Success rate",
      value: percent(successRate),
      hint:
        successRate === null
          ? "no runs recorded"
          : `${errorCount} ${errorCount === 1 ? "error" : "errors"}`,
      icon: TrendingUp,
      accent: "text-hue-emerald",
    },
    {
      label: "Avg latency",
      value: metrics && totalRuns > 0 ? duration(metrics.avg_latency_ms) : "—",
      hint: totalRuns > 0 ? "mean across all runs" : "no runs recorded",
      icon: Clock,
      accent: "text-hue-amber",
      series: latencySeries,
    },
    {
      label: "Tokens",
      value: metrics ? compactNumber(metrics.tokens.total_tokens) : "—",
      hint: metrics
        ? `${compactNumber(metrics.tokens.input_tokens)} in · ${compactNumber(metrics.tokens.output_tokens)} out`
        : "no metrics yet",
      icon: Brain,
      accent: "text-hue-violet",
      series: tokenSeries,
      tab: "analytics",
    },
    {
      label: "Memory",
      value: memory ? compactNumber(memory.total_facts) : "—",
      hint: memory
        ? `${compactNumber(memory.total_observations)} observations`
        : "no shards readable",
      icon: Database,
      accent: "text-hue-teal",
      tab: "memory",
    },
    {
      label: "Sessions",
      value: sessions ? sessions.total.toLocaleString() : "—",
      hint: criticalEvents > 0 ? `${criticalEvents} high/critical events` : "no high-severity events",
      icon: criticalEvents > 0 ? AlertTriangle : MessageSquare,
      accent: criticalEvents > 0 ? "text-hue-rose" : "text-hue-sky",
      // The hint is about audit events when there are any, so that is where
      // the tile leads; otherwise it leads to the sessions it counts.
      tab: criticalEvents > 0 ? "audit" : "sessions",
    },
  ];

  return (
    <div
      data-testid="kpi-strip"
      className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6"
    >
      {tiles.map((tile) => (
        <TileCard key={tile.label} tile={tile} onNavigate={onNavigate} />
      ))}
    </div>
  );
}

export default KpiStrip;
