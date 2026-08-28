"use client";

import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";

import { NAV_ITEMS } from "@/lib/nav";

interface ShortcutsOverlayProps {
  onClose: () => void;
}

interface Shortcut {
  keys: string[];
  description: string;
}

const GENERAL: Shortcut[] = [
  { keys: ["⌘", "K"], description: "Open the command palette" },
  { keys: ["?"], description: "Show this list" },
  { keys: ["R"], description: "Refresh every panel" },
  { keys: ["E"], description: "Export the current panel as JSON" },
  { keys: ["["], description: "Collapse or expand the sidebar" },
  { keys: ["Esc"], description: "Close a drawer, menu or overlay" },
];

function Keys({ keys }: { keys: string[] }) {
  return (
    <span className="flex shrink-0 items-center gap-1">
      {keys.map((key) => (
        <kbd
          key={key}
          className="min-w-[1.5rem] rounded border border-line-strong bg-sunken px-1.5 py-0.5 text-center font-mono text-[10px] text-fg-2"
        >
          {key}
        </kbd>
      ))}
    </span>
  );
}

function Row({ shortcut }: { shortcut: Shortcut }) {
  return (
    <li className="flex items-center justify-between gap-4 py-1.5">
      <span className="min-w-0 text-sm text-fg-2">{shortcut.description}</span>
      <Keys keys={shortcut.keys} />
    </li>
  );
}

/**
 * The keyboard reference, on `?`.
 *
 * The shortcuts existed before this did; the number keys were even described
 * in a comment in `page.tsx` while never having been implemented. A dashboard
 * whose shortcuts are only discoverable by reading its source has none.
 */
export function ShortcutsOverlay({ onClose }: ShortcutsOverlayProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
  }, []);

  // Escape closes; Tab is trapped inside the dialog so focus cannot wander
  // back onto the page behind it while it is modal.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !dialogRef.current) return;
      const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center p-4 pt-[10vh]">
      <button
        aria-label="Close keyboard shortcuts"
        onClick={onClose}
        className="absolute inset-0 h-full w-full animate-scrim-in bg-canvas/80 backdrop-blur-sm"
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="shortcuts-title"
        data-testid="shortcuts-overlay"
        className="relative z-10 max-h-[80vh] w-full max-w-2xl animate-panel-in overflow-y-auto rounded-2xl border border-line bg-panel p-6 shadow-glass backdrop-blur-xl"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 id="shortcuts-title" className="font-display text-lg font-bold text-fg">
              Keyboard shortcuts
            </h2>
            <p className="mt-0.5 text-xs text-fg-4">
              Section keys and single letters are ignored while a text field has focus.
            </p>
          </div>
          <button
            ref={closeRef}
            onClick={onClose}
            aria-label="Close keyboard shortcuts"
            className="shrink-0 rounded-lg p-1.5 text-fg-3 transition-colors hover:bg-raised/60 hover:text-fg focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <section>
            <h3 className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-fg-4">
              General
            </h3>
            <ul className="divide-y divide-line">
              {GENERAL.map((shortcut) => (
                <Row key={shortcut.description} shortcut={shortcut} />
              ))}
            </ul>
          </section>

          <section>
            <h3 className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-fg-4">
              Sections
            </h3>
            <ul className="divide-y divide-line">
              {NAV_ITEMS.map((item, index) => (
                <Row
                  key={item.id}
                  shortcut={{ keys: [String(index + 1)], description: item.label }}
                />
              ))}
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}

export default ShortcutsOverlay;
