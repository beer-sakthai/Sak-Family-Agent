"use client";

import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";

import { focusableWithin } from "@/lib/focus";

interface DrawerProps {
  title: string;
  /** Secondary line under the title — an id, a timestamp, a status. */
  subtitle?: React.ReactNode;
  icon?: React.ReactNode;
  onClose: () => void;
  children: React.ReactNode;
  "data-testid"?: string;
}

/**
 * The detail surface, shared by the session and workflow panels.
 *
 * A slide-over rather than the centred modal it replaces, for one reason that
 * matters and two that follow from it: a transcript is read *against* the list
 * it came from, and a drawer leaves that list on screen. It also gives the
 * content a tall, narrow column — the right shape for a message log — and a
 * predictable place to return focus to.
 *
 * The modal it replaces had `role="dialog"` and `aria-modal="true"` but none
 * of what those promise: no Escape handler, no focus trap, no focus return,
 * and a scrim that was a `<div onClick>` rather than anything reachable by
 * keyboard. All four are here.
 */
export function Drawer({
  title,
  subtitle,
  icon,
  onClose,
  children,
  "data-testid": testId,
}: DrawerProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  // Whatever had focus when the drawer opened, so it can be given back.
  const returnFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    returnFocusRef.current = document.activeElement as HTMLElement | null;
    closeRef.current?.focus();
    return () => {
      // The row that opened the drawer may have been re-rendered away by a
      // refresh; `focus` on a detached node is a no-op, not an error.
      returnFocusRef.current?.focus();
    };
  }, []);

  // Escape closes, Tab cycles within the panel. Registered on the document so
  // it works regardless of where inside the panel focus currently sits.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !panelRef.current) return;
      // One definition of "what Tab reaches", shared with the command palette.
      const focusable = focusableWithin(panelRef.current);
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

  // The page behind must not scroll while the drawer is open, or a trackpad
  // flick moves the list out from under the thing being read.
  useEffect(() => {
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex justify-end" data-testid={testId}>
      <button
        aria-label="Close detail"
        onClick={onClose}
        className="absolute inset-0 h-full w-full animate-scrim-in bg-canvas/70 backdrop-blur-sm"
      />

      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="relative z-10 flex h-full w-full max-w-2xl animate-drawer-in flex-col border-l border-line bg-panel shadow-glass"
      >
        <header className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
          <div className="flex min-w-0 items-start gap-2.5">
            {icon && <span className="mt-0.5 shrink-0">{icon}</span>}
            <div className="min-w-0">
              <h2 className="truncate font-display font-bold text-fg">{title}</h2>
              {subtitle && (
                <div className="mt-0.5 truncate font-mono text-[11px] text-fg-4">{subtitle}</div>
              )}
            </div>
          </div>
          <button
            ref={closeRef}
            onClick={onClose}
            aria-label="Close"
            className="shrink-0 rounded-lg p-1.5 text-fg-3 transition-colors hover:bg-raised hover:text-fg focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">{children}</div>
      </div>
    </div>
  );
}

export default Drawer;
