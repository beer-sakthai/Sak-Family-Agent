"use client";

/**
 * Chart colours, read from the same CSS variables as everything else.
 *
 * Recharts takes colours as props, not classes, so it cannot pick up the token
 * layer the way a `bg-panel` div does. Left alone the charts kept a hardcoded
 * `#1e293b` grid and a `#0f172a` tooltip — a near-black lattice over a white
 * page in light mode.
 *
 * So the values are read back out of the computed style. The alternative,
 * duplicating the palette here as literals, is the thing the token layer
 * exists to prevent: two sources for one colour, drifting apart on the next
 * theme change.
 */

import { useCallback, useSyncExternalStore } from "react";

export interface ChartTokens {
  grid: string;
  axis: string;
  tooltipBackground: string;
  tooltipBorder: string;
  tooltipText: string;
  /** Categorical series colours, in the order a chart should use them. */
  series: string[];
}

/** Dark-theme values, used for the server snapshot and if a read fails. */
const FALLBACK: ChartTokens = {
  grid: "rgb(30 41 59)",
  axis: "rgb(100 116 139)",
  tooltipBackground: "rgb(15 23 42)",
  tooltipBorder: "rgb(51 65 85)",
  tooltipText: "rgb(248 250 252)",
  series: [
    "rgb(34 211 238)",
    "rgb(52 211 153)",
    "rgb(167 139 250)",
    "rgb(251 191 36)",
    "rgb(251 113 133)",
    "rgb(56 189 248)",
  ],
};

/** `--fg-4` -> `"rgb(100 116 139)"`, or null when the variable is unset. */
function readToken(style: CSSStyleDeclaration, name: string): string | null {
  const raw = style.getPropertyValue(name).trim();
  return raw ? `rgb(${raw})` : null;
}

function readTokens(): ChartTokens {
  // jsdom returns empty strings for custom properties it was never given, and
  // a chart drawn in invisible colours is worse than one drawn in the dark
  // defaults, so every read falls back individually.
  const style = getComputedStyle(document.documentElement);
  const pick = (name: string, fallback: string) => readToken(style, name) ?? fallback;

  return {
    grid: pick("--line", FALLBACK.grid),
    axis: pick("--fg-4", FALLBACK.axis),
    tooltipBackground: pick("--panel", FALLBACK.tooltipBackground),
    tooltipBorder: pick("--line-strong", FALLBACK.tooltipBorder),
    tooltipText: pick("--fg", FALLBACK.tooltipText),
    series: [
      pick("--h-cyan", FALLBACK.series[0]),
      pick("--h-emerald", FALLBACK.series[1]),
      pick("--h-violet", FALLBACK.series[2]),
      pick("--h-amber", FALLBACK.series[3]),
      pick("--h-rose", FALLBACK.series[4]),
      pick("--h-sky", FALLBACK.series[5]),
    ],
  };
}

/**
 * Subscribe to anything that can change the resolved theme: an explicit choice
 * (which rewrites `data-theme` on `<html>`) and the OS preference (which the
 * "system" setting follows without touching the attribute).
 */
function subscribe(onChange: () => void): () => void {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
  const query = window.matchMedia("(prefers-color-scheme: light)");
  query.addEventListener("change", onChange);
  return () => {
    observer.disconnect();
    query.removeEventListener("change", onChange);
  };
}

// `useSyncExternalStore` compares snapshots by identity, so returning a fresh
// object from every read would loop forever. The snapshot is cached and only
// replaced when a subscribed event says the theme actually moved.
let cached: ChartTokens | null = null;

/** The chart palette for the theme currently rendering. */
export function useChartTokens(): ChartTokens {
  const getSnapshot = useCallback(() => {
    cached ??= readTokens();
    return cached;
  }, []);

  const subscribeAndInvalidate = useCallback((onChange: () => void) => {
    return subscribe(() => {
      cached = null;
      onChange();
    });
  }, []);

  return useSyncExternalStore(subscribeAndInvalidate, getSnapshot, () => FALLBACK);
}

/** Test seam: drop the memoised palette so the next read re-computes. */
export function clearChartTokenCache(): void {
  cached = null;
}
