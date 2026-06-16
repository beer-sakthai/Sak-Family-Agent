import { TrendingUp } from "lucide-react";

interface KPICardProps {
  label: string;
  value: number;
  delta: number;
  icon?: React.ReactNode;
}

export function KPICard({ label, value, delta, icon }: KPICardProps) {
  return (
    <div className="glow-card p-6 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-400 uppercase tracking-wide">
          {label}
        </span>
        {icon && <div className="text-cyan-400">{icon}</div>}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-4xl font-bold font-mono glow-accent">{value}</span>
        <div className="flex items-center gap-1 text-xs text-emerald-400">
          <TrendingUp className="w-3 h-3" />
          <span>+{delta}</span>
        </div>
      </div>
    </div>
  );
}
