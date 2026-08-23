"use client";

import { useState, useEffect, useCallback, useRef } from "react";

/**
 * usePanelFetch — Lightweight per-panel data-fetching hook (Custom Hook pattern).
 *
 * Replaces the repeated `useState/useEffect/fetch` lifecycle that ~16 panels
 * hand-rolled for endpoints not covered by the central `useDashboardData` bundle
 * (e.g. `/api/eval`, `/api/billing`, `/api/cache`, `/api/recovery`, …).
 *
 * Usage:
 *   const { data, loading, error, refresh } = usePanelFetch<EvalData>('/api/eval');
 *
 * @template T  Shape of the `data` field returned by the API endpoint.
 * @param apiPath  Relative API path, e.g. `/api/billing`.
 * @param options  Optional config: `immediate` (default true), `demo`, `pollIntervalMs`.
 */
export interface PanelFetchOptions {
  /** If false, the first fetch is skipped until `refresh()` is called. Default: true. */
  immediate?: boolean;
  /** When true, appends `?demo=true` to every request. */
  demo?: boolean;
  /** Optional polling interval in milliseconds. */
  pollIntervalMs?: number;
}

export interface PanelFetchResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  setData: React.Dispatch<React.SetStateAction<T | null>>;
}

export function usePanelFetch<T>(
  apiPath: string,
  options: PanelFetchOptions = {},
): PanelFetchResult<T> {
  const { immediate = true, demo = false, pollIntervalMs } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<string | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const refresh = useCallback(async () => {
    if (!isMountedRef.current) return;
    setLoading(true);
    setError(null);
    try {
      const origin =
        typeof window !== "undefined" &&
        window.location?.origin &&
        window.location.origin !== "null"
          ? window.location.origin
          : "http://localhost:3000";

      const url = `${origin}${apiPath}${demo ? (apiPath.includes("?") ? "&demo=true" : "?demo=true") : ""}`;
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const json = await res.json();
      if (!isMountedRef.current) return;
      setData(json as T);
    } catch (err) {
      if (!isMountedRef.current) return;
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      if (isMountedRef.current) setLoading(false);
    }
  }, [apiPath, demo]);

  useEffect(() => {
    if (immediate) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data fetch is the expected use of an effect
      refresh();
    }
  }, [immediate, refresh]);

  useEffect(() => {
    if (!pollIntervalMs || pollIntervalMs <= 0) return;
    const interval = setInterval(() => {
      refresh();
    }, pollIntervalMs);
    return () => clearInterval(interval);
  }, [pollIntervalMs, refresh]);

  return { data, loading, error, refresh, setData };
}
