import React from "react";

export type StatusLevel = "active" | "inactive" | "warning" | "error" | "success";

interface StatusIndicatorProps extends React.HTMLAttributes<HTMLDivElement> {
  status?: StatusLevel;
  size?: "sm" | "md" | "lg";
  label?: string;
  animated?: boolean;
}

const statusColors: Record<StatusLevel, string> = {
  active: "bg-neon-green shadow-[0_0_10px_rgb(57_255_20)]",
  inactive: "bg-fg-4 shadow-[0_0_5px_rgb(100_120_160)]",
  warning: "bg-neon-orange shadow-[0_0_10px_rgb(255_107_53)]",
  error: "bg-neon-magenta shadow-[0_0_10px_rgb(255_0_110)]",
  success: "bg-neon-green shadow-[0_0_10px_rgb(57_255_20)]",
};

const sizeClasses: Record<string, string> = {
  sm: "w-2 h-2",
  md: "w-3 h-3",
  lg: "w-4 h-4",
};

export function StatusIndicator({
  status = "active",
  size = "md",
  label,
  animated = true,
  className = "",
  ...props
}: StatusIndicatorProps) {
  const baseClasses = "rounded-full inline-block";
  const statusClass = statusColors[status];
  const sizeClass = sizeClasses[size];
  const animationClass = animated && status !== "inactive" ? "pulse-neon" : "";

  const indicator = <div className={`${baseClasses} ${sizeClass} ${statusClass} ${animationClass}`} />;

  if (label) {
    return (
      <div className={`flex items-center gap-2 ${className}`} {...props}>
        {indicator}
        <span className="text-sm font-ibm-plex-mono text-fg-2">{label}</span>
      </div>
    );
  }

  return (
    <div className={className} {...props}>
      {indicator}
    </div>
  );
}
