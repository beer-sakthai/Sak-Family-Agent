"use client";

/**
 * The dashboard's view state, in the URL.
 *
 * Previously only the section lived in the fragment; the search text, the
 * severity filter, the page number and the open transcript were React state
 * and nothing else. That made the two things people actually do with a
 * dashboard impossible: send a colleague what you are looking at, and reload
 * without losing your place.
 *
 * The whole view now serialises into the fragment as `#section?key=value`.
 * The fragment rather than the query string is deliberate — this is a static
 * client page, so a fragment change never touches the server, and
 * `useHashRoute`'s existing store already hears `hashchange` and `popstate`,
 * which is what makes the back button walk the view history.
 */

import { useCallback, useMemo } from "react";

import { PERSONA_NAMES } from "./contracts.generated";

import { useHashRoute } from "./browser-state";
import { isTabId, type TabId } from "./nav";

/** Trend windows, in days. `0` is every point the source returned. */
export const TREND_WINDOWS = [7, 14, 30, 0] as const;
export type TrendWindow = (typeof TREND_WINDOWS)[number];

export function trendWindowLabel(days: TrendWindow): string {
  return days === 0 ? "All" : `${days}d`;
}

export interface ViewState {
  tab: TabId;
  /** Free-text session search. */
  search: string;
  /** Audit severity, or "ALL". */
  severity: string;
  /** 1-based session page. */
  page: number;
  /**
   * Persona filter; empty means the whole family. Only names in
   * `PERSONA_NAMES` ever appear here — see `parseView`.
   */
  personas: string[];
  /** Open session transcript, if any. */
  session: string | null;
  /** Open workflow run, if any. */
  run: string | null;
  /** Whether sample data was explicitly requested. */
  demo: boolean;
  /** How many days of trend the analytics charts draw. */
  trend: TrendWindow;
}

export const DEFAULT_VIEW: ViewState = {
  tab: "overview",
  search: "",
  severity: "ALL",
  page: 1,
  personas: [],
  session: null,
  run: null,
  demo: false,
  trend: 30,
};

/**
 * Parse `section?key=value` into a view.
 *
 * Every field is defaulted rather than trusted: a fragment is user-editable
 * and arrives from links, so `page=-4`, `tab=nonsense` and `persona=; DROP`
 * all have to land somewhere sane instead of propagating into a fetch.
 */
export function parseView(hash: string): ViewState {
  const [rawTab, rawQuery = ""] = hash.split("?", 2);
  const params = new URLSearchParams(rawQuery);

  const page = Number.parseInt(params.get("page") ?? "", 10);
  // An unknown name is dropped rather than kept. The server's `parsePersonas`
  // already ignores anything outside PERSONA_NAMES and answers unfiltered, so
  // holding on to e.g. `?persona=sakwho` client-side would split the page
  // against itself: the lists show the whole family while AgentOverview dims
  // every card and AnalyticsCharts excludes every persona, none of them
  // matching the unknown name. Dropping it here lands a stale or mistyped
  // fragment on the documented unfiltered view everywhere at once.
  // Narrowed to the offered windows: `trend=9999` would otherwise reach the
  // slice as a number nobody chose, and `trend=abc` as NaN.
  const trend = Number.parseInt(params.get("trend") ?? "", 10);
  const known = new Set<string>(PERSONA_NAMES);
  const personas = (params.get("persona") ?? "")
    .split(",")
    .map((part) => part.trim().toLowerCase())
    .filter((part) => known.has(part));

  return {
    tab: isTabId(rawTab) ? rawTab : DEFAULT_VIEW.tab,
    search: params.get("q") ?? DEFAULT_VIEW.search,
    severity: params.get("severity") ?? DEFAULT_VIEW.severity,
    page: Number.isFinite(page) && page > 0 ? page : DEFAULT_VIEW.page,
    // Deduplicated; already narrowed to PERSONA_NAMES above.
    personas: [...new Set(personas)],
    session: params.get("session") || null,
    run: params.get("run") || null,
    demo: params.get("demo") === "1",
    trend: (TREND_WINDOWS as readonly number[]).includes(trend)
      ? (trend as TrendWindow)
      : DEFAULT_VIEW.trend,
  };
}

/**
 * Serialise a view back to a fragment, omitting everything at its default.
 *
 * Omitting defaults is what keeps `#overview` readable instead of
 * `#overview?q=&severity=ALL&page=1&demo=0`, and it means two ways of
 * reaching the same view produce the same URL.
 */
export function serializeView(view: ViewState): string {
  const params = new URLSearchParams();
  if (view.search) params.set("q", view.search);
  if (view.severity !== DEFAULT_VIEW.severity) params.set("severity", view.severity);
  if (view.page > 1) params.set("page", String(view.page));
  if (view.personas.length > 0) params.set("persona", view.personas.join(","));
  if (view.session) params.set("session", view.session);
  if (view.run) params.set("run", view.run);
  if (view.demo) params.set("demo", "1");
  if (view.trend !== DEFAULT_VIEW.trend) params.set("trend", String(view.trend));

  const encoded = params.toString();
  return encoded ? `${view.tab}?${encoded}` : view.tab;
}

/**
 * The view, read from and written to the URL fragment.
 *
 * `patch` takes a partial view so a caller changes one field without
 * restating the rest, and resets dependent fields itself where a change
 * invalidates them (a new search invalidates the page number).
 */
export function useViewState(): [ViewState, (patch: Partial<ViewState>) => void] {
  const [hash, setHash] = useHashRoute(DEFAULT_VIEW.tab);

  // Parsing is cheap, but the result is a fresh object every render, and it
  // feeds the `useCallback` deps of every fetch in the page. Memoising on the
  // string keeps those callbacks stable between renders.
  const view = useMemo(() => parseView(hash), [hash]);

  const patch = useCallback(
    (next: Partial<ViewState>) => {
      setHash(serializeView({ ...parseView(hash), ...next }));
    },
    [hash, setHash],
  );

  return [view, patch];
}
