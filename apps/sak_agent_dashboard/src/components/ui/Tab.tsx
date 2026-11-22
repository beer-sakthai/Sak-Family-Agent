import React from "react";

interface TabProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  neon?: boolean;
  children: React.ReactNode;
}

interface TabGroupProps {
  children: React.ReactNode;
  className?: string;
}

export function Tab({
  active = false,
  neon = true,
  className = "",
  children,
  ...props
}: TabProps) {
  const baseClasses =
    "px-4 py-2 font-orbitron font-900 tracking-wider uppercase text-sm transition-all duration-200 relative";

  const activeClass = active
    ? neon
      ? "text-neon-cyan border-b-2 border-neon-cyan shadow-[0_0_8px_rgb(0_245_255/0.3)]"
      : "text-fg border-b-2 border-accent"
    : "text-fg-3 border-b-2 border-transparent hover:text-fg-2";

  return (
    <button className={`${baseClasses} ${activeClass} ${className}`} {...props}>
      {children}
    </button>
  );
}

export function TabGroup({ children, className = "" }: TabGroupProps) {
  return (
    <div className={`flex gap-1 border-b border-line ${className}`}>
      {children}
    </div>
  );
}
