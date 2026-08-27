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

import type { MetricsPayload, PersonasPayload } from "@/lib/contracts.generated";

interface AnalyticsChartsProps {
  metrics: MetricsPayload;
  personas?: PersonasPayload;
}

const COLORS = ["#06b6d4", "#10b981", "#8b5cf6", "#f59e0b", "#f43f5e", "#38bdf8"];

const TOOLTIP_STYLE = {
  backgroundColor: "#0f172a",
  borderColor: "#334155",
  borderRadius: "0.5rem",
  color: "#f8fafc",
};

/** Rendered in place of a chart that has nothing real to show. */
function EmptyChart({ label }: { label: string }) {
  return (
    <div className="h-64 w-full flex items-center justify-center text-xs font-mono text-slate-500 border border-dashed border-slate-800 rounded-xl">
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
    <div className="glass-panel p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`p-2 rounded-lg border ${accent}`}>{icon}</div>
          <h4 className="text-sm font-bold font-display text-slate-200">{title}</h4>
        </div>
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
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

export function AnalyticsCharts({ metrics, personas }: AnalyticsChartsProps) {
  const isMounted = useHydrated();

  // Every series below is derived from real data or omitted. The previous
  // version filled gaps with hardcoded numbers and, for a persona with no
  // score, `Math.floor(Math.random() * 15 + 85)` -- which made the render
  // non-deterministic and the chart fiction.
  const activePersonas = (personas?.personas ?? []).filter((p) => p.runs > 0);

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

  const successRate = metrics.total_runs > 0 ? (1 - metrics.error_rate) * 100 : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight">
            Performance & Run Analytics
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Token distribution, latency trends, and execution outcomes from the eval log
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-cyan-400">
            Total runs: <strong className="text-white">{metrics.total_runs.toLocaleString()}</strong>
          </span>
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-emerald-400">
            Success rate:{" "}
            <strong className="text-white">
              {successRate === null ? "—" : `${successRate.toFixed(1)}%`}
            </strong>
          </span>
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-amber-400">
            Avg latency:{" "}
            <strong className="text-white">{Math.round(metrics.avg_latency_ms)}ms</strong>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel
          title="Success Rate by Persona (%)"
          source="eval.jsonl"
          accent="bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
          icon={<BarChart3 className="h-4 w-4" />}
        >
          {!isMounted ? null : successData.length === 0 ? (
            <EmptyChart label="No attributed runs yet" />
          ) : (
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <BarChart data={successData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} tickLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="success" fill="#06b6d4" radius={[6, 6, 0, 0]} name="Success %" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Panel>

        <Panel
          title="Token Usage by Persona"
          source="eval.jsonl"
          accent="bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
          icon={<Zap className="h-4 w-4" />}
        >
          {!isMounted ? null : tokenData.length === 0 ? (
            <EmptyChart label="No attributed runs yet" />
          ) : (
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <AreaChart data={tokenData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Area
                  type="monotone"
                  dataKey="input"
                  stackId="1"
                  stroke="#06b6d4"
                  fill="#06b6d4"
                  fillOpacity={0.3}
                  name="Input"
                />
                <Area
                  type="monotone"
                  dataKey="output"
                  stackId="1"
                  stroke="#10b981"
                  fill="#10b981"
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
          accent="bg-violet-500/10 text-violet-400 border-violet-500/20"
          icon={<TrendingUp className="h-4 w-4" />}
        >
          {!isMounted ? null : trendData.length === 0 ? (
            <EmptyChart label="No runs recorded yet" />
          ) : (
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <LineChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="runs" stroke="#06b6d4" strokeWidth={2} dot={false} name="Runs" />
                <Line
                  type="monotone"
                  dataKey="latency"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={false}
                  name="Latency (ms)"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Panel>

        <Panel
          title="Stop Reason Breakdown"
          source="eval.jsonl"
          accent="bg-amber-500/10 text-amber-400 border-amber-500/20"
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
                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={TOOLTIP_STYLE} />
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
