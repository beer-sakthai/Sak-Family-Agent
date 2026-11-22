import React from "react";

interface ChartWrapperProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  neonBorder?: boolean;
  accentColor?: "cyan" | "magenta" | "purple" | "green" | "orange";
  children: React.ReactNode;
}

const accentClasses: Record<string, string> = {
  cyan: "border-neon-cyan shadow-[inset_0_0_15px_rgb(0_245_255/0.1),0_0_20px_rgb(0_245_255/0.2)]",
  magenta: "border-neon-magenta shadow-[inset_0_0_15px_rgb(255_0_110/0.1),0_0_20px_rgb(255_0_110/0.2)]",
  purple: "border-neon-purple shadow-[inset_0_0_15px_rgb(181_55_242/0.1),0_0_20px_rgb(181_55_242/0.2)]",
  green: "border-neon-green shadow-[inset_0_0_15px_rgb(57_255_20/0.1),0_0_20px_rgb(57_255_20/0.2)]",
  orange: "border-neon-orange shadow-[inset_0_0_15px_rgb(255_107_53/0.1),0_0_20px_rgb(255_107_53/0.2)]",
};

export function ChartWrapper({
  title,
  neonBorder = true,
  accentColor = "cyan",
  className = "",
  children,
  ...props
}: ChartWrapperProps) {
  const baseClasses = "bg-panel rounded-sm";

  const borderClass = neonBorder
    ? `border border-opacity-60 ${accentClasses[accentColor]}`
    : "border border-line";

  return (
    <div className={`${baseClasses} ${borderClass} ${className}`} {...props}>
      {title && (
        <div className="border-b border-line-soft px-4 py-2">
          <h3 className="text-sm font-orbitron font-900 tracking-wider uppercase text-neon-cyan drop-shadow-[0_0_8px_rgb(0_245_255/0.3)]">
            {title}
          </h3>
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}
