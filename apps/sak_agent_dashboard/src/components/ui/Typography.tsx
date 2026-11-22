import React from "react";

interface HeadingProps extends React.HTMLAttributes<HTMLHeadingElement> {
  level?: 1 | 2 | 3 | 4 | 5 | 6;
  neon?: boolean;
  children: React.ReactNode;
}

interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  neon?: boolean;
  children: React.ReactNode;
}

interface BodyProps extends React.HTMLAttributes<HTMLParagraphElement> {
  size?: "sm" | "md" | "lg";
  muted?: boolean;
  monospace?: boolean;
  children: React.ReactNode;
}

const headingClasses: Record<number, string> = {
  1: "text-4xl font-space-mono font-bold tracking-wider",
  2: "text-3xl font-orbitron font-900 tracking-wider uppercase",
  3: "text-2xl font-orbitron font-900 tracking-wide uppercase",
  4: "text-xl font-orbitron font-900 tracking-wide uppercase",
  5: "text-lg font-ibm-plex-mono font-600 tracking-wide",
  6: "text-base font-ibm-plex-mono font-600 tracking-wide",
};

const neonClasses = "text-neon-cyan drop-shadow-[0_0_10px_rgb(0_245_255/0.5)]";

export function Heading({
  level = 2,
  neon = false,
  className = "",
  children,
  ...props
}: HeadingProps) {
  const Tag = `h${level}` as const;
  const baseClass = headingClasses[level];
  const neonClass = neon ? neonClasses : "text-fg";

  return (
    <Tag className={`${baseClass} ${neonClass} ${className}`} {...props}>
      {children}
    </Tag>
  );
}

export function Label({ neon = false, className = "", children, ...props }: LabelProps) {
  const baseClass = "text-sm font-orbitron font-900 tracking-wider uppercase";
  const neonClass = neon ? "text-neon-cyan" : "text-fg-2";

  return (
    <label className={`${baseClass} ${neonClass} ${className}`} {...props}>
      {children}
    </label>
  );
}

export function Body({
  size = "md",
  muted = false,
  monospace = true,
  className = "",
  children,
  ...props
}: BodyProps) {
  const sizeClasses: Record<string, string> = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-lg",
  };

  const textClass = muted ? "text-fg-3" : "text-fg";
  const fontClass = monospace ? "font-ibm-plex-mono" : "font-sans";

  return (
    <p className={`${sizeClasses[size]} ${textClass} ${fontClass} ${className}`} {...props}>
      {children}
    </p>
  );
}

/**
 * Convenience export for inline text with neon styling
 */
export function NeonText({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <span className={`text-neon-cyan drop-shadow-[0_0_8px_rgb(0_245_255/0.4)] ${className}`}>{children}</span>;
}
