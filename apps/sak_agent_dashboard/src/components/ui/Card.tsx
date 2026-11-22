import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  neonBorder?: boolean;
  techGrid?: boolean;
  accentColor?: "cyan" | "magenta" | "purple" | "green" | "orange";
  children: React.ReactNode;
}

const accentClasses: Record<string, string> = {
  cyan: "border-neon-cyan shadow-[inset_0_0_15px_rgb(0_245_255/0.2),0_0_20px_rgb(0_245_255/0.3)]",
  magenta: "border-neon-magenta shadow-[inset_0_0_15px_rgb(255_0_110/0.2),0_0_20px_rgb(255_0_110/0.3)]",
  purple: "border-neon-purple shadow-[inset_0_0_15px_rgb(181_55_242/0.2),0_0_20px_rgb(181_55_242/0.3)]",
  green: "border-neon-green shadow-[inset_0_0_15px_rgb(57_255_20/0.2),0_0_20px_rgb(57_255_20/0.3)]",
  orange: "border-neon-orange shadow-[inset_0_0_15px_rgb(255_107_53/0.2),0_0_20px_rgb(255_107_53/0.3)]",
};

export function Card({
  neonBorder = true,
  techGrid = true,
  accentColor = "cyan",
  className = "",
  children,
  ...props
}: CardProps) {
  const baseClasses = "bg-panel rounded-sm";

  const borderClass = neonBorder
    ? `border border-opacity-80 ${accentClasses[accentColor]}`
    : "border border-line";

  const gridClass = techGrid ? "tech-grid" : "";

  const neonBorderPulseClass = neonBorder ? "neon-border-pulse" : "";

  return (
    <div
      className={`${baseClasses} ${borderClass} ${gridClass} ${neonBorderPulseClass} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
