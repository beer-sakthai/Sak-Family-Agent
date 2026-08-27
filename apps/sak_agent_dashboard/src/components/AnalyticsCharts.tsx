"use client";

import React, { useSyncExternalStore } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BarChart3, PieChart as PieIcon, TrendingUp, Zap } from "lucide-react";

import { useChartTokens } from "@/lib/chart-theme";
import type { MetricsPayload, PersonasPayload } from "@/lib/contracts.generated";

interface AnalyticsChartsProps {
  metrics: MetricsPayload;
  personas?: PersonasPayload;
  /** The global persona filter; empty means the whole family. */
  selectedPersonas?: string[];
}

/** Rendered in place of a chart that has nothing real to show. */
function EmptyChart({ label }: { label: string }) {
  return (
    <div className="h-64 w-full flex items-center justify-center text-xs font-mono text-fg-4 border border-dashed border-line rounded-xl">
      {label}
    </div>
  );
}

function Panel({
  title,
  source,
  icon,
  accent,
  children,
}: {
  title: string;
  source: string;
  icon: React.ReactNode;
  accent: string;
  children: React.ReactNode;
}) {
  return (
    <div className="glass-panel p-5 rounded-2xl bg-panel/80 border border-line/80 backdrop-blur-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`p-2 rounded-lg border ${accent}`}>{icon}</div>
          <h4 className="text-sm font-bold font-display text-fg">{title}</h4>
        </div>
        <span className="text-[10px] font-mono text-fg-4 uppercase tracking-wider">
          {source}
        </span>
      </div>
      <div className="h-64 w-full">{children}</div>
    </div>
  );
}

/**
 * True once hydrated, false during SSR.
 *
 * Recharts measures its container, so it can only render client-side. This is
 * the `useSyncExternalStore` form of that gate rather than
 * `useEffect(() => setMounted(true))`, which schedules a second render pass on
 * every mount (and which `react-hooks/set-state-in-effect` rightly flags).
 * The store never changes, so `subscribe` has nothing to unsubscribe.
 */
function useHydrated(): boolean {
  return useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}

export function AnalyticsCharts({
  metrics,
  personas,
  selectedPersonas = [],
}: AnalyticsChartsProps) {
  const isMounted = useHydrated();
  // Colours come from the same CSS variables as the rest of the UI; Recharts
  // takes them as props, so they are read rather than applied as classes.
  const chart = useChartTokens();

  const tooltipStyle = {
    backgroundColor: chart.tooltipBackground,
    borderColor: chart.tooltipBorder,
    borderRadius: "0.5rem",
    color: chart.tooltipText,
  };

  // Every series below is derived from real data or omitted. The previous
  // version filled gaps with hardcoded numbers and, for a persona with no
  // score, `Math.floor(Math.random() * 15 + 85)` -- which made the render
  // non-deterministic and the chart fiction.
  // A persona with no runs has nothing to plot; the global filter narrows
  // further, so the per-persona charts describe the same set the rest of the
  // page does rather than quietly showing all six.
  const activePersonas = (personas?.personas ?? []).filter(
    (p) => p.runs > 0 && (selectedPersonas.length === 0 || selectedPersonas.includes(p.name)),
  );

  const successData = activePersonas.map((p) => ({
    name: p.display_name,
    success: Number((((p.runs - p.errors) / p.runs) * 100).toFixed(1)),
    latency: Math.round(p.avg_latency_ms),
  }));

  const tokenData = activePersonas.map((p) => ({
    name: p.display_name,
    input: p.input_tokens,
    output: p.output_tokens,
  }));

  const stopReasonData = Object.entries(metrics.stop_reasons).map(([name, value]) => ({
    name,
    value,
  }));

  const trendData = metrics.trends.map((point) => ({
    date: point.date.slice(5), // MM-DD is enough on a crowded axis
    runs: point.runs,
    errors: point.errors,
    latency: Math.round(point.avg_latency_ms),
  }));

  return (
    <div className="space-y-6">
      {/* The title, the description and the three headline figures that used to
          sit here are all on screen already — in the topbar and the KPI strip
          above. What only this view can say is how many personas its per-persona
          charts are actually drawn from. */}
      <div className="flex flex-wrap items-center justify-end gap-2">
        <span className="rounded-full border border-line bg-panel px-3 py-1 font-mono text-xs text-fg-3">
          {selectedPersonas.length > 0
            ? `${activePersonas.length} of ${selectedPersonas.length} filtered personas have attributed runs`
            : `${activePersonas.length} of ${personas?.personas.length ?? 0} personas have attributed runs`}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel
          title="Success Rate by Persona (%)"
          source="eval.jsonl"
          accent="bg-hue-cyan/10 text-hue-cyan border-hue-cyan-line/20"
          icon={<BarChart3 className="h-4 w-4" />}
        >
          {!isMounted ? null : successData.length === 0 ? (
            <EmptyChart label="No attributed runs yet" />
          ) : (
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <BarChart data={successData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={chart.grid} />
                <XAxis dataKey="name" stroke={chart.axis} fontSize={11} tickLine={false} />
                <YAxis stroke={chart.axis} fontSize={11} domain={[0, 100]} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="success" fill={chart.series[0]} radius={[6, 6, 0, 0]} name="Success %" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Panel>

        <Panel
          title="Token Usage by Persona"
          source="eval.jsonl"
          accent="bg-hue-emerald/10 text-hue-emerald border-hue-emerald-line/20"
          icon={<Zap className="h-4 w-4" />}
        >
          {!isMounted ? null : tokenData.length === 0 ? (
            <EmptyChart label="No attributed runs yet" />
          ) : (
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <AreaChart data={tokenData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={chart.grid} />
                <XAxis dataKey="name" stroke={chart.axis} fontSize={11} tickLine={false} />
                <YAxis stroke={chart.axis} fontSize={11} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Area
                  type="monotone"
                  dataKey="input"
                  stackId="1"
                  stroke={chart.series[0]}
                  fill={chart.series[0]}
                  fillOpacity={0.3}
                  name="Input"
                />
                <Area
                  type="monotone"
                  dataKey="output"
                  stackId="1"
                  stroke={chart.series[1]}
                  fill={chart.series[1]}
                  fillOpacity={0.3}
                  name="Output"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Panel>

        <Panel
          title="Runs & Latency Over Time"
          source="eval.jsonl"
          accent="bg-hue-violet/10 text-hue-violet border-hue-violet-line/20"
          icon={<TrendingUp className="h-4 w-4" />}
        >
          {!isMounted ? null : trendData.length === 0 ? (
            <EmptyChart label="No runs recorded yet" />
          ) : (
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <LineChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={chart.grid} />
                <XAxis dataKey="date" stroke={chart.axis} fontSize={11} tickLine={false} />
                <YAxis stroke={chart.axis} fontSize={11} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="runs" stroke={chart.series[0]} strokeWidth={2} dot={false} name="Runs" />
                <Line
                  type="monotone"
                  dataKey="latency"
                  stroke={chart.series[3]}
                  strokeWidth={2}
                  dot={false}
                  name="Latency (ms)"
                />
                {/* `errors` was computed into trendData and never drawn. It is
                    the one series here that says whether the runs beside it
                    actually worked. */}
                <Line
                  type="monotone"
                  dataKey="errors"
                  stroke={chart.series[4]}
                  strokeWidth={2}
                  strokeDasharray="4 3"
                  dot={false}
                  name="Errors"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Panel>

        <Panel
          title="Stop Reason Breakdown"
          source="eval.jsonl"
          accent="bg-hue-amber/10 text-hue-amber border-hue-amber-line/20"
          icon={<PieIcon className="h-4 w-4" />}
        >
          {!isMounted ? null : stopReasonData.length === 0 ? (
            <EmptyChart label="No runs recorded yet" />
          ) : (
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <PieChart>
                <Pie
                  data={stopReasonData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  innerRadius={45}
                  paddingAngle={2}
                >
                  {stopReasonData.map((entry, index) => (
                    <Cell key={entry.name} fill={chart.series[index % chart.series.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Panel>
      </div>
    </div>
  );
}

export default AnalyticsCharts;
