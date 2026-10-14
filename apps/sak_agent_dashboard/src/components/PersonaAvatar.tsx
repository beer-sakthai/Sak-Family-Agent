import React from "react";
import { Cpu } from "lucide-react";

import { PERSONA_NAMES } from "@/lib/contracts.generated";

/**
 * Every persona has a portrait at `public/personas/<name>.svg`.
 *
 * The SVGs are copies of `docs/images/personas/` at the repo root — the same
 * pictures the README shows. Vercel builds this app from its own directory, so
 * it cannot reach `docs/`; `persona-avatar.test.tsx` keeps the copies identical
 * and fails if a persona joins `PERSONA_NAMES` without one.
 */
const PORTRAITS: ReadonlySet<string> = new Set(PERSONA_NAMES);

interface PersonaAvatarProps {
  /** Canonical lowercase persona name, e.g. `sakthai`. */
  name: string;
  /** Rendered width and height in pixels. */
  size?: number;
  className?: string;
}

/**
 * A persona's portrait, or a neutral chip for a name without one.
 *
 * Decorative by default (`alt=""`): every place that shows it also shows the
 * persona's name as text, so a screen reader would only hear it twice.
 */
export function PersonaAvatar({ name, size = 40, className = "" }: PersonaAvatarProps) {
  if (!PORTRAITS.has(name)) {
    return (
      <span
        data-testid={`persona-avatar-${name}`}
        style={{ width: size, height: size }}
        className={`inline-flex shrink-0 items-center justify-center rounded-xl border border-line-strong/50 bg-raised/80 ${className}`}
      >
        <Cpu className="h-1/2 w-1/2 text-hue-cyan" aria-hidden="true" />
      </span>
    );
  }
  return (
    // A plain <img>: next/image would route a 2 KB static SVG through the image
    // optimiser, which refuses SVG unless `dangerouslyAllowSVG` is switched on.
    // eslint-disable-next-line @next/next/no-img-element
    <img
      data-testid={`persona-avatar-${name}`}
      src={`/personas/${name}.svg`}
      width={size}
      height={size}
      alt=""
      decoding="async"
      className={`shrink-0 rounded-xl ${className}`}
    />
  );
}

export default PersonaAvatar;
