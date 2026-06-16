import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { GrowthData } from "@/hooks/useDashboardData";

interface GrowthChartProps {
  data: GrowthData;
}

export function GrowthChart({ data }: GrowthChartProps) {
  const chartData = data.labels.map((label, i) => ({
    date: label,
    facts: data.facts[i],
    observations: data.observations[i],
  }));

  return (
    <div className="glow-card p-6">
      <h2 className="text-lg font-semibold font-mono glow-text mb-4">Cumulative Growth</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#232a3a" />
          <XAxis dataKey="date" stroke="#8b94a7" style={{ fontSize: "0.75rem" }} />
          <YAxis stroke="#8b94a7" style={{ fontSize: "0.75rem" }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#141d3a",
              border: "1px solid #232a3a",
              borderRadius: "0.5rem",
            }}
            labelStyle={{ color: "#e6e9f0" }}
          />
          <Legend wrapperStyle={{ paddingTop: "1rem" }} />
          <Line
            type="monotone"
            dataKey="facts"
            stroke="#00d9ff"
            strokeWidth={2}
            dot={false}
            isAnimationActive={true}
            animationDuration={800}
          />
          <Line
            type="monotone"
            dataKey="observations"
            stroke="#d946ef"
            strokeWidth={2}
            dot={false}
            isAnimationActive={true}
            animationDuration={800}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
