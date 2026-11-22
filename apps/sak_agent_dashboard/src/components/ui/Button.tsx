import React from "react";

export type ButtonVariant = "primary" | "secondary" | "tertiary" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  neon?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-neon-cyan text-black hover:bg-opacity-80 neon-glow",
  secondary: "bg-panel border border-line-strong text-fg hover:bg-raised",
  tertiary: "bg-transparent text-fg hover:bg-raised/50",
  danger: "bg-neon-magenta text-black hover:bg-opacity-80 neon-glow",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "px-2 py-1 text-xs font-ibm-plex-mono",
  md: "px-4 py-2 text-sm font-ibm-plex-mono",
  lg: "px-6 py-3 text-base font-ibm-plex-mono",
};

export function Button({
  variant = "primary",
  size = "md",
  neon = true,
  disabled = false,
  className = "",
  ...props
}: ButtonProps) {
  const baseClasses =
    "inline-flex items-center justify-center rounded-sm font-medium transition-all duration-200 focus-visible:outline-2 outline-offset-2 focus-visible:outline-neon-cyan disabled:opacity-50 disabled:cursor-not-allowed";

  const variantClass = variantClasses[variant];
  const sizeClass = sizeClasses[size];
  const neonClass = neon && variant !== "secondary" && variant !== "tertiary" ? "neon-glow-focus" : "";

  return (
    <button
      className={`${baseClasses} ${variantClass} ${sizeClass} ${neonClass} ${className}`}
      disabled={disabled}
      {...props}
    />
  );
}
