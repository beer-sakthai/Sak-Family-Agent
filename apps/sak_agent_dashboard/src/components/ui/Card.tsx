import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  neonBorder?: boolean;
  techGrid?: boolean;
  accentColor?: "cyan" | "magenta" | "purple" | "green" | "orange";
  children: React.ReactNode;
}

export function Card({
  neonBorder = true,
  techGrid = true,
  accentColor = "cyan",
  className = "",
  children,
  ...props
}: CardProps) {
  const baseClasses = "bg-panel rounded-sm";

  const neonCardClass = neonBorder ? `neon-card neon-card-${accentColor}` : "border border-line";
  const gridClass = techGrid ? "tech-grid" : "";

  return (
    <div
      className={`${baseClasses} ${neonCardClass} ${gridClass} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
