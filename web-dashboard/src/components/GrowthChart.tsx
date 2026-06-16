import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Growth } from "../types";

export function GrowthChart({ growth }: { growth: Growth }) {
  const rows = growth.labels.map((label, i) => ({
    date: label,
    facts: growth.facts[i] ?? 0,
    observations: growth.observations[i] ?? 0,
  }));

  return (
    <div className="card">
      <h2 className="card-title">Cumulative memory growth</h2>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={rows} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="gFacts" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#a855f7" stopOpacity={0.5} />
              <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gObs" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.5} />
              <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="date" tick={{ fill: "#8b949e", fontSize: 11 }} minTickGap={28} />
          <YAxis tick={{ fill: "#8b949e", fontSize: 11 }} allowDecimals={false} width={42} />
          <Tooltip
            contentStyle={{
              background: "#0b0e14",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 12,
              color: "#e6edf3",
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Area
            type="monotone"
            dataKey="facts"
            stroke="#a855f7"
            strokeWidth={2}
            fill="url(#gFacts)"
          />
          <Area
            type="monotone"
            dataKey="observations"
            stroke="#22d3ee"
            strokeWidth={2}
            fill="url(#gObs)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
