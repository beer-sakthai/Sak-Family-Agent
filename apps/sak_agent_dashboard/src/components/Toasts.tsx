"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { AlertTriangle, Check, Info, X } from "lucide-react";

export type ToastTone = "success" | "error" | "info";

export interface Toast {
  id: number;
  tone: ToastTone;
  message: string;
}

const TONE_STYLES: Record<ToastTone, { icon: typeof Check; classes: string }> = {
  success: {
    icon: Check,
    classes: "border-hue-emerald-line bg-hue-emerald-tint/80 text-hue-emerald",
  },
  error: {
    icon: AlertTriangle,
    classes: "border-hue-rose-line bg-hue-rose-tint/80 text-hue-rose",
  },
  info: { icon: Info, classes: "border-line bg-panel/90 text-fg-2" },
};

const DISMISS_AFTER_MS = 4_000;

/**
 * A small toast queue.
 *
 * Actions that succeed quietly — an export, a copied link, a refresh with no
 * visible change — used to give no feedback at all, which reads as the button
 * not working. Errors that were previously only a banner at the top of a
 * scrolled page get seen here too.
 */
export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(1);
  // Timers are tracked so unmounting mid-flight cannot fire setState on a
  // component that is gone.
  const timers = useRef(new Set<number>());

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const push = useCallback(
    (tone: ToastTone, message: string) => {
      const id = nextId.current++;
      setToasts((current) => [...current, { id, tone, message }]);
      const timer = window.setTimeout(() => {
        timers.current.delete(timer);
        dismiss(id);
      }, DISMISS_AFTER_MS);
      timers.current.add(timer);
    },
    [dismiss],
  );

  useEffect(() => {
    const pending = timers.current;
    return () => {
      for (const timer of pending) window.clearTimeout(timer);
      pending.clear();
    };
  }, []);

  return { toasts, push, dismiss };
}

/**
 * The toast stack.
 *
 * `aria-live="polite"` on the container, not on each toast: the region has to
 * exist in the DOM before a message lands in it, or screen readers announce
 * nothing.
 */
export function ToastStack({
  toasts,
  onDismiss,
}: {
  toasts: Toast[];
  onDismiss: (id: number) => void;
}) {
  return (
    <div
      aria-live="polite"
      aria-atomic="false"
      data-testid="toast-stack"
      className="pointer-events-none fixed bottom-4 right-4 z-[70] flex w-full max-w-sm flex-col gap-2"
    >
      {toasts.map((toast) => {
        const { icon: Icon, classes } = TONE_STYLES[toast.tone];
        return (
          <div
            key={toast.id}
            role={toast.tone === "error" ? "alert" : "status"}
            className={`pointer-events-auto flex animate-toast-in items-start gap-2.5 rounded-xl border px-3.5 py-2.5 text-sm shadow-glass backdrop-blur-xl ${classes}`}
          >
            <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
            <span className="min-w-0 flex-1">{toast.message}</span>
            <button
              onClick={() => onDismiss(toast.id)}
              aria-label="Dismiss notification"
              className="shrink-0 rounded p-0.5 opacity-60 transition-opacity hover:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <X className="h-3 w-3" aria-hidden />
            </button>
          </div>
        );
      })}
    </div>
  );
}

export default ToastStack;
