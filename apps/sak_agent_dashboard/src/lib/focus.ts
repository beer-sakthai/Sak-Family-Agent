"use client";

/**
 * Two pieces of keyboard behaviour the shell needs and neither modal nor
 * tablist should reimplement.
 *
 * `focusableWithin` is the single answer to "what would Tab reach in here",
 * shared by the drawer and the command palette — the selector was previously
 * inline in `Drawer.tsx` and nowhere else, so the palette had no trap at all.
 */

import { useCallback, useEffect, useRef, useState } from "react";

const FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

/**
 * Best-effort "would a Tab reach this".
 *
 * Deliberately not `offsetParent !== null`, the usual shorthand: it depends on
 * layout, and jsdom performs none — every element reports null there, so a
 * trap built on it would silently degrade to a one-element list under test and
 * only a real browser would ever exercise the wrapping path.
 */
function isVisible(element: HTMLElement): boolean {
  if (element.hidden || element.getAttribute("aria-hidden") === "true") return false;
  if (element.closest("[hidden]") !== null) return false;
  const style = typeof window === "undefined" ? null : window.getComputedStyle(element);
  return !style || (style.display !== "none" && style.visibility !== "hidden");
}

export function focusableWithin(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(isVisible);
}

/**
 * Trap Tab inside a modal and give focus back when it closes.
 *
 * Attach the returned ref to the modal's container. The handler is on the
 * container rather than the document, so two overlapping modals cannot fight
 * over Tab: the innermost one holds focus, so its handler sees the event.
 */
export function useFocusTrap<T extends HTMLElement>(): React.RefObject<T | null> {
  const containerRef = useRef<T | null>(null);

  // Captured in a state initialiser rather than an effect: React applies
  // `autoFocus` during the commit phase, so by the time any effect runs the
  // modal's own field already holds focus and the opener is lost. An
  // initialiser runs during the first render, before that.
  const [returnTo] = useState<Element | null>(() =>
    typeof document === "undefined" ? null : document.activeElement,
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const focusable = focusableWithin(container);
      if (focusable.length === 0) return;

      const first = focusable[0]!;
      const last = focusable[focusable.length - 1]!;
      const active = document.activeElement;

      if (event.shiftKey && (active === first || !container.contains(active))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };

    container.addEventListener("keydown", onKeyDown);

    return () => {
      container.removeEventListener("keydown", onKeyDown);
      // Only take focus back if the modal still had it. Closing by clicking
      // something else on the page should leave focus where the click put it.
      if (
        returnTo instanceof HTMLElement &&
        (document.activeElement === document.body || container.contains(document.activeElement))
      ) {
        returnTo.focus();
      }
    };
  }, [returnTo]);

  return containerRef;
}

/**
 * Roving tabindex over a list of controls.
 *
 * A tablist should be one tab stop with the arrows moving between its tabs —
 * WAI-ARIA's authoring practice, and the difference between one Tab to reach
 * the panel and seven. Returns a ref registrar and the list's key handler.
 */
export function useRovingFocus(
  count: number,
  activeIndex: number,
  onActivate: (index: number) => void,
) {
  const itemsRef = useRef<(HTMLElement | null)[]>([]);

  const register = useCallback(
    (index: number) => (element: HTMLElement | null) => {
      itemsRef.current[index] = element;
    },
    [],
  );

  const onKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      const deltas: Record<string, number> = {
        ArrowDown: 1,
        ArrowRight: 1,
        ArrowUp: -1,
        ArrowLeft: -1,
      };
      let next: number | null = null;

      if (event.key in deltas) {
        next = (activeIndex + deltas[event.key]! + count) % count;
      } else if (event.key === "Home") {
        next = 0;
      } else if (event.key === "End") {
        next = count - 1;
      }

      if (next === null) return;
      event.preventDefault();
      onActivate(next);
      itemsRef.current[next]?.focus();
    },
    [activeIndex, count, onActivate],
  );

  return { register, onKeyDown };
}
