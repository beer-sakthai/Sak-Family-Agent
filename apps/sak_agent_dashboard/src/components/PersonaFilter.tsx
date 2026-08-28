"use client";

import React, { useEffect, useRef, useState } from "react";
import { Check, Users, X } from "lucide-react";

import { PERSONA_NAMES } from "@/lib/contracts.generated";
import { displayName } from "@/lib/persona";

interface PersonaFilterProps {
  /** Selected persona names; empty means the whole family. */
  selected: string[];
  onChange: (next: string[]) => void;
  /** Run counts per persona, when known, so the menu shows who is active. */
  counts?: Record<string, number>;
}

/**
 * The family filter.
 *
 * Multi-select rather than a single-persona dropdown because the interesting
 * comparisons here are between two or three personas, not one against the
 * whole family. Empty selection means everyone — which is the default, and
 * why the trigger reads "All personas" rather than showing nothing selected.
 *
 * The selection reaches the API as `?persona=a,b`; the sessions and memory
 * routes apply it at the source, so counts and paging describe the filtered
 * set rather than a filtered page of an unfiltered count.
 */
export function PersonaFilter({ selected, onChange, counts }: PersonaFilterProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

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

  const toggle = (name: string) => {
    onChange(
      selected.includes(name) ? selected.filter((item) => item !== name) : [...selected, name],
    );
  };

  const label =
    selected.length === 0
      ? "All personas"
      : selected.length === 1
        ? displayName(selected[0])
        : `${selected.length} personas`;

  return (
    <div ref={containerRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-haspopup="menu"
        data-testid="persona-filter"
        className={`inline-flex items-center gap-1.5 rounded-xl border px-2.5 py-1.5 font-mono text-[11px] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
          selected.length > 0
            ? "border-hue-cyan-line bg-hue-cyan-tint/50 text-hue-cyan"
            : "border-line bg-panel/60 text-fg-3 hover:border-line-strong hover:text-fg-2"
        }`}
      >
        <Users className="h-3 w-3" aria-hidden />
        {label}
        {selected.length > 0 && (
          // A nested <button> would be invalid inside the trigger, so the
          // clear affordance is a focusable span with an explicit role.
          <span
            role="button"
            tabIndex={0}
            aria-label="Clear persona filter"
            onClick={(event) => {
              event.stopPropagation();
              onChange([]);
            }}
            onKeyDown={(event) => {
              if (event.key !== "Enter" && event.key !== " ") return;
              event.preventDefault();
              event.stopPropagation();
              onChange([]);
            }}
            className="-mr-0.5 ml-0.5 rounded p-0.5 hover:bg-hue-cyan-tint focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <X className="h-3 w-3" aria-hidden />
          </span>
        )}
      </button>

      {open && (
        <div
          role="menu"
          aria-label="Filter by persona"
          className="absolute right-0 z-50 mt-2 w-56 rounded-2xl border border-line bg-panel p-2 shadow-glass backdrop-blur-xl"
        >
          <button
            role="menuitem"
            onClick={() => onChange([])}
            className={`mb-1 flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
              selected.length === 0
                ? "bg-raised text-fg"
                : "text-fg-3 hover:bg-raised/60 hover:text-fg-2"
            }`}
          >
            <Users className="h-3.5 w-3.5 shrink-0" aria-hidden />
            <span className="flex-1 text-left">All personas</span>
            {selected.length === 0 && <Check className="h-3.5 w-3.5 text-accent" aria-hidden />}
          </button>

          <div className="my-1 border-t border-line" />

          {PERSONA_NAMES.map((name) => {
            const checked = selected.includes(name);
            const count = counts?.[name];
            return (
              <button
                key={name}
                role="menuitemcheckbox"
                aria-checked={checked}
                onClick={() => toggle(name)}
                className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                  checked ? "bg-raised text-fg" : "text-fg-3 hover:bg-raised/60 hover:text-fg-2"
                }`}
              >
                <span
                  aria-hidden
                  className={`grid h-3.5 w-3.5 shrink-0 place-items-center rounded border ${
                    checked ? "border-accent bg-accent" : "border-line-strong"
                  }`}
                >
                  {checked && <Check className="h-2.5 w-2.5 text-accent-contrast" />}
                </span>
                <span className="flex-1 text-left">{displayName(name)}</span>
                {count !== undefined && (
                  <span className="font-mono text-[10px] text-fg-4">{count}</span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default PersonaFilter;
