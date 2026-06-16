import { TrendingUp, TrendingDown } from "lucide-react";
import { LineChart, Line, ResponsiveContainer } from "recharts";

interface KPICardProps {
  label: string;
  value: number;
  delta: number;
  icon?: React.ReactNode;
  sparklineData?: number[];
  description?: string;
}

export function KPICard({
  label,
  value,
  delta,
  icon,
  sparklineData,
  description,
}: KPICardProps) {
  const isPositive = delta >= 0;
  const sparkData = sparklineData?.map((v, i) => ({ value: v })) || [];

  return (
    <div className="glow-card p-6 flex flex-col gap-4 hover:shadow-lg hover:shadow-cyan-500/30 transition-all duration-300">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-widest">
            {label}
          </span>
          {description && (
            <span className="text-xs text-slate-500 font-normal">{description}</span>
          )}
        </div>
        {icon && <div className="text-cyan-400 opacity-80">{icon}</div>}
      </div>

      {/* Main Value */}
      <div className="flex items-baseline gap-3">
        <span className="text-5xl font-bold font-mono glow-accent tracking-tighter">
          {value.toLocaleString()}
        </span>
        <div
          className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-md ${
            isPositive
              ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20"
              : "text-red-400 bg-red-500/10 border border-red-500/20"
          }`}
        >
          {isPositive ? (
            <TrendingUp className="w-3.5 h-3.5" />
          ) : (
            <TrendingDown className="w-3.5 h-3.5" />
          )}
          <span>{isPositive ? "+" : ""}{delta}</span>
        </div>
      </div>

      {/* Sparkline Chart */}
      {sparkData.length > 0 && (
        <div className="h-12 -mx-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparkData}>
              <Line
                type="monotone"
                dataKey="value"
                stroke="#00d9ff"
                strokeWidth={2}
                dot={false}
                isAnimationActive={true}
                animationDuration={1000}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Footer Info */}
      <div className="pt-2 border-t border-slate-700/30 flex items-center justify-between text-xs text-slate-500">
        <span>This week</span>
        <span className="font-mono">+{delta} new</span>
      </div>
    </div>
  );
}
