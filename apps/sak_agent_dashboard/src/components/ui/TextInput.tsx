import React from "react";

interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  neon?: boolean;
  error?: boolean;
  label?: string;
}

export function TextInput({
  neon = true,
  error = false,
  label,
  className = "",
  ...props
}: TextInputProps) {
  const baseClasses =
    "bg-sunken text-fg font-ibm-plex-mono text-sm rounded-sm px-3 py-2 transition-all duration-200 placeholder-fg-4";

  const borderClass = error
    ? "border border-neon-magenta"
    : neon
      ? "border border-line-soft focus:border-neon-cyan"
      : "border border-line focus:border-accent";

  return (
    <div>
      {label && <label className="block text-sm font-orbitron font-900 tracking-wider uppercase text-fg-2 mb-1">{label}</label>}
      <input
        className={`${baseClasses} ${borderClass} ${className}`}
        {...props}
      />
    </div>
  );
}
