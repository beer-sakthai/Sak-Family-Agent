import React from "react";

export type BadgeColor = "cyan" | "magenta" | "purple" | "green" | "orange";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  color?: BadgeColor;
  size?: "sm" | "md" | "lg";
  children: React.ReactNode;
}

const colorClasses: Record<BadgeColor, string> = {
  cyan: "bg-cyan-900 text-neon-cyan border border-neon-cyan",
  magenta: "bg-rose-900 text-neon-magenta border border-neon-magenta",
  purple: "bg-purple-900 text-neon-purple border border-neon-purple",
  green: "bg-green-900 text-neon-green border border-neon-green",
  orange: "bg-orange-900 text-neon-orange border border-neon-orange",
};

const sizeClasses: Record<string, string> = {
  sm: "px-2 py-1 text-xs",
  md: "px-3 py-1.5 text-sm",
  lg: "px-4 py-2 text-base",
};

export function Badge({
  color = "cyan",
  size = "md",
  className = "",
  children,
  ...props
}: BadgeProps) {
  const baseClasses = "inline-flex items-center justify-center rounded-sm font-orbitron font-900 tracking-wider uppercase";

  return (
    <span
      className={`${baseClasses} ${colorClasses[color]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
