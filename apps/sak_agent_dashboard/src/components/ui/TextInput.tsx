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
    ? "border border-neon-magenta focus:border-neon-magenta focus:shadow-[inset_0_0_8px_rgb(255_0_110/0.2),0_0_12px_rgb(255_0_110/0.3)]"
    : neon
      ? "border border-line-soft focus:border-neon-cyan focus:shadow-[inset_0_0_8px_rgb(0_245_255/0.2),0_0_12px_rgb(0_245_255/0.3)]"
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
