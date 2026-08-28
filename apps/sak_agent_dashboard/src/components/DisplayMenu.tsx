"use client";

import React, { useEffect, useRef, useState } from "react";
import { Check, Monitor, Moon, Rows3, Rows4, Settings2, Sun } from "lucide-react";

import { resolveTheme, THEMES, type Density, type Theme } from "@/lib/theme";

interface DisplayMenuProps {
  theme: Theme;
  onThemeChange: (next: Theme) => void;
  density: Density;
  onDensityChange: (next: Density) => void;
  /** What "system" currently resolves to, for the trigger's icon. */
  prefersLight: boolean;
}

const THEME_ICONS: Record<Theme, typeof Sun> = {
  system: Monitor,
  light: Sun,
  dark: Moon,
};

const THEME_LABELS: Record<Theme, string> = {
  system: "Match system",
  light: "Light",
  dark: "Dark",
};

/**
 * Appearance settings — theme and density — behind one topbar control.
 *
 * A popover rather than two more buttons in a row that already holds five:
 * these are set-once preferences, not things reached on every visit.
 */
export function DisplayMenu({
  theme,
  onThemeChange,
  density,
  onDensityChange,
  prefersLight,
}: DisplayMenuProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // Close on Escape or on a click outside. Both listeners are attached only
  // while the menu is open, so a closed menu costs nothing.
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.stopPropagation();
      setOpen(false);
      triggerRef.current?.focus();
    };
    const onPointerDown = (event: PointerEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };

    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("pointerdown", onPointerDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("pointerdown", onPointerDown);
    };
  }, [open]);

  // The trigger shows what you are looking at, not what is configured: on
  // "system" that is the resolved appearance, so the icon never contradicts
  // the page around it.
  const TriggerIcon = THEME_ICONS[theme === "system" ? (prefersLight ? "light" : "dark") : theme];

  return (
    <div ref={containerRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label="Display settings"
        title="Display settings"
        className="inline-flex items-center gap-1.5 rounded-xl border border-line bg-panel/60 px-2.5 py-1.5 text-fg-3 transition-colors hover:border-line-strong hover:text-fg-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        <TriggerIcon className="h-3.5 w-3.5" aria-hidden />
        <Settings2 className="h-3 w-3 opacity-60" aria-hidden />
      </button>

      {open && (
        <div
          role="menu"
          aria-label="Display settings"
          className="absolute right-0 z-50 mt-2 w-56 rounded-2xl border border-line bg-panel p-2 shadow-glass backdrop-blur-xl"
        >
          <p className="px-2 pb-1.5 pt-1 text-[10px] font-semibold uppercase tracking-wider text-fg-4">
            Theme
          </p>
          {THEMES.map((option) => {
            const Icon = THEME_ICONS[option];
            const selected = theme === option;
            return (
              <button
                key={option}
                role="menuitemradio"
                aria-checked={selected}
                onClick={() => onThemeChange(option)}
                className={`flex w-full items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                  selected ? "bg-raised text-fg" : "text-fg-3 hover:bg-raised/60 hover:text-fg-2"
                }`}
              >
                <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden />
                <span className="flex-1 text-left">{THEME_LABELS[option]}</span>
                {option === "system" && (
                  <span className="font-mono text-[10px] text-fg-4">
                    {resolveTheme("system", prefersLight)}
                  </span>
                )}
                {selected && <Check className="h-3.5 w-3.5 shrink-0 text-accent" aria-hidden />}
              </button>
            );
          })}

          <div className="my-1.5 border-t border-line" />

          <p className="px-2 pb-1.5 pt-1 text-[10px] font-semibold uppercase tracking-wider text-fg-4">
            Density
          </p>
          {(
            [
              ["comfortable", "Comfortable", Rows3],
              ["compact", "Compact", Rows4],
            ] as const
          ).map(([option, label, Icon]) => {
            const selected = density === option;
            return (
              <button
                key={option}
                role="menuitemradio"
                aria-checked={selected}
                onClick={() => onDensityChange(option)}
                className={`flex w-full items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                  selected ? "bg-raised text-fg" : "text-fg-3 hover:bg-raised/60 hover:text-fg-2"
                }`}
              >
                <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden />
                <span className="flex-1 text-left">{label}</span>
                {selected && <Check className="h-3.5 w-3.5 shrink-0 text-accent" aria-hidden />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default DisplayMenu;
