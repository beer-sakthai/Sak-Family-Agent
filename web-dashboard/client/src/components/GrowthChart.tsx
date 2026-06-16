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
import { Card } from "@/components/ui/card";

interface GrowthChartProps {
  data: GrowthData;
}

export function GrowthChart({ data }: GrowthChartProps) {
  const chartData = data.labels.map((label, i) => ({
    date: label,
    facts: data.facts[i],
    observations: data.observations[i],
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900/95 border border-cyan-500/30 rounded-lg p-3 backdrop-blur-sm shadow-lg">
          <p className="text-xs text-slate-400 font-mono mb-2">{payload[0].payload.date}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm font-mono">
              {entry.name}: <span className="font-bold">{entry.value}</span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="p-6 border-cyan-500/30 bg-slate-900/50 hover:border-cyan-500/60 transition-all duration-300">
      <div className="mb-4">
        <h2 className="text-xl font-bold font-mono glow-accent mb-1">Cumulative Growth</h2>
        <p className="text-xs text-slate-500">Memory accumulation over time</p>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="colorFacts" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00d9ff" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#00d9ff" stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="colorObs" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#d946ef" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#d946ef" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false} />
          <XAxis dataKey="date" stroke="#8b94a7" style={{ fontSize: "12px" }} tick={{ fill: "#8b94a7" }} />
          <YAxis stroke="#8b94a7" style={{ fontSize: "12px" }} tick={{ fill: "#8b94a7" }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ paddingTop: "20px" }} iconType="line" contentStyle={{ background: "transparent", border: "none" }} labelStyle={{ color: "#e6e9f0", fontSize: "12px" }} />
          <Line
            type="monotone"
            dataKey="facts"
            stroke="#00d9ff"
            strokeWidth={3}
            dot={{ fill: "#00d9ff", r: 4 }}
            activeDot={{ r: 6, fill: "#00d9ff" }}
            isAnimationActive={true}
            animationDuration={800}
            animationEasing="ease-in-out"
            name="Facts"
            fillOpacity={1}
            fill="url(#colorFacts)"
          />
          <Line
            type="monotone"
            dataKey="observations"
            stroke="#d946ef"
            strokeWidth={3}
            dot={{ fill: "#d946ef", r: 4 }}
            activeDot={{ r: 6, fill: "#d946ef" }}
            isAnimationActive={true}
            animationDuration={800}
            animationEasing="ease-in-out"
            name="Observations"
            fillOpacity={1}
            fill="url(#colorObs)"
          />
        </LineChart>
      </ResponsiveContainer>
      <div className="mt-6 pt-4 border-t border-slate-700/30 grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <span className="text-xs text-slate-500 uppercase tracking-wide">Total Facts</span>
          <span className="text-lg font-bold font-mono text-cyan-400">
            {chartData[chartData.length - 1]?.facts || 0}
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-xs text-slate-500 uppercase tracking-wide">Total Observations</span>
          <span className="text-lg font-bold font-mono text-purple-400">
            {chartData[chartData.length - 1]?.observations || 0}
          </span>
        </div>
      </div>
    </Card>
  );
}
