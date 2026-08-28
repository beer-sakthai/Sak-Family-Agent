"use client";

/**
 * Browser-owned state — the URL fragment and `localStorage` — read the way
 * React wants external stores read.
 *
 * The obvious alternative, `useState(fallback)` plus an effect that reads the
 * real value on mount, has two problems this avoids: it schedules a second
 * render on every mount (which `react-hooks/set-state-in-effect` flags), and
 * between the two renders the UI shows the fallback. `useSyncExternalStore`
 * has an explicit server snapshot, so the server and the hydrating client
 * agree, and React re-renders once with the real value afterwards.
 */

import { useCallback, useEffect, useSyncExternalStore } from "react";

import {
  applyDensity,
  applyPresentation,
  applyTheme,
  DENSITY_STORAGE_KEY,
  isDensity,
  isTheme,
  PRESENTATION_STORAGE_KEY,
  THEME_STORAGE_KEY,
  type Density,
  type Theme,
} from "./theme";

type Listener = () => void;

const listeners = new Set<Listener>();

function emit(): void {
  for (const listener of listeners) listener();
}

function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  // `storage` covers another tab changing the same key; `hashchange` and
  // `popstate` cover the back button.
  window.addEventListener("storage", listener);
  window.addEventListener("hashchange", listener);
  window.addEventListener("popstate", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
    window.removeEventListener("hashchange", listener);
    window.removeEventListener("popstate", listener);
  };
}

function readStorage(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    // Private mode, or site data blocked. A missing preference is not an error.
    return null;
  }
}

function writeStorage(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Ignore: the preference simply will not survive a reload.
  }
}

/**
 * A string preference persisted to `localStorage`.
 *
 * Returns the fallback during SSR and for any unreadable or unset key, so a
 * caller never has to handle `null`.
 */
export function usePersistedString(
  key: string,
  fallback: string,
): [string, (value: string) => void] {
  const value = useSyncExternalStore(
    subscribe,
    () => readStorage(key) ?? fallback,
    () => fallback,
  );

  const setValue = useCallback(
    (next: string) => {
      writeStorage(key, next);
      emit();
    },
    [key],
  );

  return [value, setValue];
}

/**
 * The URL fragment, as a route.
 *
 * Assigning `location.hash` (rather than `history.pushState`) is deliberate:
 * it pushes a history entry *and* fires `hashchange`, so the back button moves
 * between sections and the store above hears about it without a manual event.
 */
export function useHashRoute(fallback: string): [string, (next: string) => void] {
  const hash = useSyncExternalStore(
    subscribe,
    () => window.location.hash.replace(/^#/, ""),
    () => "",
  );

  const setHash = useCallback((next: string) => {
    if (window.location.hash.replace(/^#/, "") === next) return;
    window.location.hash = next;
    // `location.hash` updates synchronously but `hashchange` is dispatched on a
    // later task, so notify now: without this the section lags the URL by a
    // frame on every navigation. The event still arrives and re-reads the same
    // value, which is a no-op.
    emit();
  }, []);

  return [hash || fallback, setHash];
}

/**
 * The theme preference, kept in sync with the `data-theme` attribute.
 *
 * The attribute is already correct on arrival — the inline bootstrap in
 * `layout.tsx` sets it before first paint — so the effect here is not what
 * makes the first render right. It exists to re-apply the attribute when the
 * preference *changes*, including from another tab, which the `storage`
 * listener in `subscribe` above surfaces.
 */
export function useTheme(): [Theme, (next: Theme) => void] {
  const [raw, setRaw] = usePersistedString(THEME_STORAGE_KEY, "system");
  const theme: Theme = isTheme(raw) ? raw : "system";

  useEffect(() => {
    applyTheme(theme, document.documentElement);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => setRaw(next), [setRaw]);
  return [theme, setTheme];
}

/** The density preference, same contract as `useTheme`. */
export function useDensity(): [Density, (next: Density) => void] {
  const [raw, setRaw] = usePersistedString(DENSITY_STORAGE_KEY, "comfortable");
  const density: Density = isDensity(raw) ? raw : "comfortable";

  useEffect(() => {
    applyDensity(density, document.documentElement);
  }, [density]);

  const setDensity = useCallback((next: Density) => setRaw(next), [setRaw]);
  return [density, setDensity];
}

/**
 * Presentation mode, same contract as `useTheme`.
 *
 * A boolean rather than a string union: there is no third state, and the
 * stored value is only ever compared against "on".
 */
export function usePresentation(): [boolean, (next: boolean) => void] {
  const [raw, setRaw] = usePersistedString(PRESENTATION_STORAGE_KEY, "off");
  const presenting = raw === "on";

  useEffect(() => {
    applyPresentation(presenting, document.documentElement);
  }, [presenting]);

  const setPresenting = useCallback((next: boolean) => setRaw(next ? "on" : "off"), [setRaw]);
  return [presenting, setPresenting];
}

/**
 * Whether the OS currently asks for a light palette.
 *
 * Only needed to render the *resolved* appearance of the "system" setting —
 * the CSS follows the media query on its own. Returns false during SSR, which
 * matches the dark-first default the server renders.
 */
export function usePrefersLight(): boolean {
  return useSyncExternalStore(
    (listener) => {
      const query = window.matchMedia("(prefers-color-scheme: light)");
      query.addEventListener("change", listener);
      return () => query.removeEventListener("change", listener);
    },
    () => window.matchMedia("(prefers-color-scheme: light)").matches,
    () => false,
  );
}
