"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";

import AgentOverview from "@/components/AgentOverview";
import AnalyticsCharts from "@/components/AnalyticsCharts";
import AuditLogs from "@/components/AuditLogs";
import CommandPalette, { type Command } from "@/components/CommandPalette";
import HostedNotice from "@/components/HostedNotice";
import KpiStrip from "@/components/KpiStrip";
import MemoryExplorer from "@/components/MemoryExplorer";
import PersonaDrawer from "@/components/PersonaDrawer";
import SessionExplorer from "@/components/SessionExplorer";
import Sidebar from "@/components/shell/Sidebar";
import TopBar, { REFRESH_INTERVALS, type RefreshInterval } from "@/components/shell/TopBar";
import ShortcutsOverlay from "@/components/ShortcutsOverlay";
import { CardGridSkeleton, KpiSkeleton, PanelSkeleton } from "@/components/Skeletons";
import StitchStudio from "@/components/StitchStudio";
import { ToastStack, useToasts } from "@/components/Toasts";
import WorkflowRuns from "@/components/WorkflowRuns";
import {
  useDensity,
  usePresentation,
  usePersistedString,
  usePrefersLight,
  useTheme,
} from "@/lib/browser-state";
import type {
  ApiEnvelope,
  AuditPayload,
  DataSource,
  MemoryPayload,
  MetricsPayload,
  PersonasPayload,
  SessionDetail,
  SessionsPayload,
  WorkflowRunDetail,
  WorkflowsPayload,
} from "@/lib/contracts.generated";
import { downloadFile, exportFilename, toCsv } from "@/lib/export";
import { NAV_ITEMS, navItem, type TabId } from "@/lib/nav";
import { DENSITIES, THEMES } from "@/lib/theme";
import { useViewState } from "@/lib/url-state";

const PAGE_SIZE = 10;

const STORAGE_KEYS = {
  collapsed: "sak-dashboard:sidebar-collapsed",
  refresh: "sak-dashboard:refresh-interval",
} as const;

/**
 * Fetch one envelope. Returns null on failure rather than substituting demo
 * data: which source is in play is the API's decision, reported back in
 * `source`, and the UI shows it. Quietly swapping in fiction here is exactly
 * what made the old dashboard untrustworthy.
 */
async function fetchEnvelope<T>(url: string): Promise<ApiEnvelope<T> | null> {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as ApiEnvelope<T>;
  } catch {
    return null;
  }
}

/** Narrow a stored preference to one of the offered intervals. */
function parseInterval(raw: string): RefreshInterval {
  const parsed = Number(raw);
  return (REFRESH_INTERVALS as readonly number[]).includes(parsed)
    ? (parsed as RefreshInterval)
    : 0;
}

export default function Home() {
  // The whole view — section, filters, page, open detail, demo flag — lives in
  // the URL fragment, so it is linkable, survives a reload, and the back button
  // walks it. See `lib/url-state.ts`.
  const [view, patchView] = useViewState();
  const {
    tab: activeTab,
    search,
    severity,
    page,
    personas,
    session: sessionId,
    run: runId,
    agent: agentName,
    trend,
  } = view;
  const isDemo = view.demo;

  const [collapsedPref, setCollapsedPref] = usePersistedString(STORAGE_KEYS.collapsed, "off");
  const sidebarCollapsed = collapsedPref === "on";

  const [refreshPref, setRefreshPref] = usePersistedString(STORAGE_KEYS.refresh, "0");
  const refreshInterval = parseInterval(refreshPref);

  // Appearance. Both are already applied to <html> by the bootstrap script
  // in layout.tsx; these hooks own changing them.
  const [theme, setTheme] = useTheme();
  const [density, setDensity] = useDensity();
  const [presenting, setPresenting] = usePresentation();
  const prefersLight = usePrefersLight();

  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());

  const { toasts, push: pushToast, dismiss: dismissToast } = useToasts();

  const [personasPayload, setPersonasPayload] = useState<PersonasPayload | null>(null);
  const [metrics, setMetrics] = useState<MetricsPayload | null>(null);
  const [memory, setMemory] = useState<MemoryPayload | null>(null);
  const [audit, setAudit] = useState<AuditPayload | null>(null);
  const [sessions, setSessions] = useState<SessionsPayload | null>(null);
  const [workflows, setWorkflows] = useState<WorkflowsPayload | null>(null);
  const [activeSource, setActiveSource] = useState<DataSource | null>(null);

  const [sessionDetail, setSessionDetail] = useState<{
    id: string;
    detail: SessionDetail | null;
  } | null>(null);
  const [runDetail, setRunDetail] = useState<{
    id: string;
    detail: WorkflowRunDetail | null;
  } | null>(null);

  // The persona filter is a string in the URL and an array here; joining it
  // once keeps it out of every `useCallback` dependency list as a new array.
  const personaParam = personas.join(",");

  const buildQs = useCallback(
    (includePersona: boolean, extra: Record<string, string | number | null>) => {
      const params = new URLSearchParams();
      if (isDemo) params.set("demo", "1");
      if (includePersona && personaParam) params.set("persona", personaParam);
      for (const [key, value] of Object.entries(extra)) {
        if (value !== null && value !== "" && value !== "ALL") params.set(key, String(value));
      }
      const encoded = params.toString();
      return encoded ? `?${encoded}` : "";
    },
    [isDemo, personaParam],
  );

  /** For the routes that honour the persona filter: metrics, sessions, memory, audit. */
  const qs = useCallback(
    (extra: Record<string, string | number | null> = {}) => buildQs(true, extra),
    [buildQs],
  );

  /**
   * For the routes with no persona dimension to filter on.
   *
   * `/api/agents` must return all six personas whatever the filter — the
   * overview dims the excluded cards rather than dropping them, and the filter
   * menu needs every name to offer. `/api/workflows` reads one directory that
   * records no persona at all, so a `?persona=` there would be ignored; sending
   * it anyway would imply a narrowing that never happens.
   */
  const qsFamilyWide = useCallback(
    (extra: Record<string, string | number | null> = {}) => buildQs(false, extra),
    [buildQs],
  );

  // No state is set before the first `await`: the effect below calls this, and
  // a synchronous setState inside an effect schedules a cascading render.
  // The Refresh button sets `isLoading` itself, which is an event handler and
  // therefore fine.
  const refresh = useCallback(async () => {
    const [personasRes, metricsRes, memoryRes, auditRes, sessionsRes, workflowsRes] =
      await Promise.all([
        fetchEnvelope<PersonasPayload>(`/api/agents${qsFamilyWide()}`),
        fetchEnvelope<MetricsPayload>(`/api/metrics${qs()}`),
        fetchEnvelope<MemoryPayload>(`/api/memory${qs()}`),
        fetchEnvelope<AuditPayload>(`/api/audit${qs({ severity })}`),
        fetchEnvelope<SessionsPayload>(
          `/api/sessions${qs({ search, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE })}`,
        ),
        fetchEnvelope<WorkflowsPayload>(`/api/workflows${qsFamilyWide()}`),
      ]);

    if (personasRes) {
      setPersonasPayload(personasRes.data);
      setActiveSource(personasRes.source);
    }
    if (metricsRes) setMetrics(metricsRes.data);
    if (memoryRes) setMemory(memoryRes.data);
    if (auditRes) setAudit(auditRes.data);
    if (sessionsRes) setSessions(sessionsRes.data);
    if (workflowsRes) setWorkflows(workflowsRes.data);

    setError(
      !personasRes && !metricsRes
        ? "Could not reach the dashboard API. Check the server and try again."
        : null,
    );
    setLastUpdatedAt(Date.now());
    setIsLoading(false);
  }, [qs, qsFamilyWide, search, page, severity]);

  useEffect(() => {
    // refresh() sets no state before its first `await`, so nothing here runs
    // synchronously; the rule cannot see through the useCallback to tell.
    // Fetching on mount is the intended use of an effect.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  // Auto-refresh. Off by default; the interval is a stored preference, so a
  // wall-mounted tab keeps polling across a reload.
  useEffect(() => {
    if (refreshInterval === 0) return;
    const timer = window.setInterval(() => void refresh(), refreshInterval * 1_000);
    return () => window.clearInterval(timer);
  }, [refreshInterval, refresh]);

  // Ages the "3m ago" label without re-fetching anything.
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 10_000);
    return () => window.clearInterval(timer);
  }, []);

  // Session and workflow detail are fetched on demand rather than up front —
  // a transcript is large and only one is ever open at a time.
  //
  // Neither effect clears state synchronously on the way out; the "nothing
  // selected" case is derived at render instead (see `activeSessionDetail`),
  // so a stale detail can never be shown for a newly selected id.
  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    void fetchEnvelope<SessionsPayload>(`/api/sessions${qs({ id: sessionId })}`).then((res) => {
      if (!cancelled) setSessionDetail({ id: sessionId, detail: res?.data.detail ?? null });
    });
    return () => {
      cancelled = true;
    };
  }, [sessionId, qs]);

  useEffect(() => {
    if (!runId) return;
    let cancelled = false;
    void fetchEnvelope<WorkflowRunDetail | null>(`/api/workflows${qsFamilyWide({ id: runId })}`).then(
      (res) => {
        if (!cancelled) setRunDetail({ id: runId, detail: res?.data ?? null });
      },
    );
    return () => {
      cancelled = true;
    };
  }, [runId, qsFamilyWide]);

  const goToTab = useCallback(
    (nextTab: TabId) => {
      // A section change clears the open detail: a transcript id means nothing
      // on the memory panel, and leaving it in the URL would reopen the drawer
      // on the way back.
      patchView({ tab: nextTab, session: null, run: null, agent: null });
    },
    [patchView],
  );

  const handleRefresh = useCallback(() => {
    setIsLoading(true);
    void refresh();
  }, [refresh]);

  const toggleDemo = useCallback(
    (next: boolean) => {
      patchView({ demo: next, page: 1 });
    },
    [patchView],
  );

  const setPersonas = useCallback(
    (next: string[]) => {
      // Narrowing the family can leave the current page past the end of the
      // filtered set, which would render an empty page with a pager saying
      // otherwise. Back to the first page.
      //
      // The open transcript goes too. Only the summary rows are filtered by
      // persona -- the detail is fetched by id and would keep rendering, so a
      // SakSee transcript would sit open over a page claiming to show only
      // SakThai. Runs stay: `getWorkflows` takes no persona, so a run detail
      // is still valid under any filter.
      patchView({ personas: next, page: 1, session: null });
    },
    [patchView],
  );

  /**
   * The persona whose drawer is open, resolved against the payload rather than
   * trusted from the URL. `parseView` already narrows the name to the known
   * six, but a name can be known and still absent from a payload that has not
   * arrived yet — in which case there is simply no drawer, not an empty one.
   */
  const activePersona = useMemo(
    () => personasPayload?.personas.find((item) => item.name === agentName) ?? null,
    [personasPayload, agentName],
  );

  const openPersona = useCallback(
    (name: string) => patchView({ agent: name }),
    [patchView],
  );

  const togglePersona = useCallback(
    (name: string) =>
      setPersonas(
        personas.includes(name) ? personas.filter((item) => item !== name) : [...personas, name],
      ),
    [personas, setPersonas],
  );

  /** What the active panel holds, as rows plus the columns a CSV should use. */
  const exportable = useMemo((): {
    rows: Record<string, unknown>[];
    columns: string[];
  } | null => {
    switch (activeTab) {
      case "overview":
        return personasPayload
          ? {
              rows: personasPayload.personas as unknown as Record<string, unknown>[],
              columns: [
                "name",
                "display_name",
                "provider",
                "model",
                "runs",
                "errors",
                "avg_latency_ms",
                "input_tokens",
                "output_tokens",
                "fact_count",
                "observation_count",
                "has_shard",
                "last_run_at",
              ],
            }
          : null;
      case "analytics":
        return metrics
          ? {
              rows: metrics.trends as unknown as Record<string, unknown>[],
              columns: [
                "date",
                "runs",
                "errors",
                "avg_latency_ms",
                "input_tokens",
                "output_tokens",
              ],
            }
          : null;
      case "sessions":
        return sessions
          ? {
              rows: sessions.sessions as unknown as Record<string, unknown>[],
              columns: [
                "id",
                "timestamp",
                "persona",
                "task",
                "model",
                "iterations",
                "stop_reason",
                "message_count",
                "tool_call_count",
                "had_error",
              ],
            }
          : null;
      case "memory":
        return memory
          ? {
              rows: memory.facts as unknown as Record<string, unknown>[],
              columns: ["id", "persona", "kind", "key", "value", "tags", "created_at", "updated_at"],
            }
          : null;
      case "workflows":
        return workflows
          ? {
              rows: workflows.runs as unknown as Record<string, unknown>[],
              columns: [
                "run_id",
                "workflow_name",
                "status",
                "started_at",
                "finished_at",
                "duration_seconds",
                "step_count",
                "failed_steps",
              ],
            }
          : null;
      case "audit":
        return audit
          ? {
              rows: audit.events as unknown as Record<string, unknown>[],
              columns: ["timestamp", "type", "severity", "message", "details"],
            }
          : null;
      // The Stitch panel reads no runtime data, so there is nothing to export.
      default:
        return null;
    }
  }, [activeTab, personasPayload, metrics, sessions, memory, workflows, audit]);

  const handleExport = useCallback(
    (format: "json" | "csv") => {
      if (!exportable || exportable.rows.length === 0) {
        pushToast("info", `Nothing to export from ${navItem(activeTab).label}.`);
        return;
      }
      const { rows, columns } = exportable;
      const content =
        format === "json"
          ? JSON.stringify(rows, null, 2)
          : toCsv(rows, columns as (keyof (typeof rows)[number] & string)[]);
      downloadFile(
        exportFilename(activeTab, format),
        content,
        format === "json" ? "application/json" : "text/csv",
      );
      pushToast(
        "success",
        `Exported ${rows.length} ${rows.length === 1 ? "row" : "rows"} as ${format.toUpperCase()}.`,
      );
    },
    [exportable, activeTab, pushToast],
  );

  const handleCopyLink = useCallback(() => {
    // The fragment already carries the whole view, so the current href is the
    // shareable link with no assembly needed.
    navigator.clipboard
      .writeText(window.location.href)
      .then(() => pushToast("success", "Link to this view copied."))
      .catch(() => pushToast("error", "Could not copy to the clipboard."));
  }, [pushToast]);

  // Keyboard. ⌘K/Ctrl+K for the palette, digits for sections, `r` refresh,
  // `e` export, `[` sidebar, `?` help, Escape out of presentation mode.
  // Suppressed while typing, so a search field never eats a shortcut.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const typing =
        target instanceof HTMLElement &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT" ||
          target.isContentEditable);

      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((open) => !open);
        return;
      }
      if (typing || event.metaKey || event.ctrlKey || event.altKey) return;

      // The digits were described in a comment here for a long time without
      // ever being implemented. They are 1-based over the same NAV_ITEMS the
      // sidebar renders, so the numbering matches what is on screen.
      const digit = Number.parseInt(event.key, 10);
      if (Number.isFinite(digit) && digit >= 1 && digit <= NAV_ITEMS.length) {
        event.preventDefault();
        goToTab(NAV_ITEMS[digit - 1].id);
        return;
      }

      switch (event.key) {
        case "r":
          event.preventDefault();
          handleRefresh();
          break;
        case "e":
          event.preventDefault();
          handleExport("json");
          break;
        case "[":
          event.preventDefault();
          setCollapsedPref(sidebarCollapsed ? "off" : "on");
          break;
        case "?":
          event.preventDefault();
          setShortcutsOpen((open) => !open);
          break;
        case "Escape":
          // The one way out that needs no visible control, which is the point
          // of a mode that hides the controls.
          if (presenting) {
            event.preventDefault();
            setPresenting(false);
          }
          break;
        default:
          break;
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [
    handleRefresh,
    handleExport,
    goToTab,
    sidebarCollapsed,
    setCollapsedPref,
    presenting,
    setPresenting,
  ]);

  /**
   * The palette's data rows — the personas, the loaded sessions and the loaded
   * memory facts, each as a command that opens the thing it names.
   *
   * This is what makes ⌘K a search rather than a menu. Before it, finding a
   * transcript meant going to Sessions, typing into the search field and
   * waiting for a round trip; the rows here are already in the browser, so the
   * palette answers as you type and the Enter opens the drawer directly.
   *
   * Deliberately drawn from what is loaded rather than from a new query: a
   * palette that fetched its own results could offer a session the list behind
   * it does not contain, and picking one would land on a page that then has to
   * explain itself. The cap keeps the unfiltered palette a menu — the fuzzy
   * ranker reaches the rest as soon as there is a query.
   */
  const dataCommands = useMemo<Command[]>(() => {
    const rows: Command[] = [];

    for (const persona of personasPayload?.personas ?? []) {
      rows.push({
        id: `persona-${persona.name}`,
        label: persona.display_name,
        hint: `${persona.runs} run${persona.runs === 1 ? "" : "s"} · ${persona.model || "no configured model"}`,
        group: "Personas",
        run: () => {
          goToTab("overview");
          openPersona(persona.name);
        },
      });
    }

    for (const session of (sessions?.sessions ?? []).slice(0, 12)) {
      rows.push({
        id: `session-${session.id}`,
        label: session.task || session.id,
        hint: `${session.persona ?? "unattributed"} · ${session.model} · ${session.stop_reason}`,
        group: "Sessions",
        run: () => patchView({ tab: "sessions", session: session.id, run: null, agent: null }),
      });
    }

    for (const fact of (memory?.facts ?? []).slice(0, 12)) {
      rows.push({
        id: `fact-${fact.id}`,
        label: fact.key ?? fact.value.slice(0, 60),
        hint: `${fact.persona} · ${fact.kind}`,
        group: "Memory",
        run: () => goToTab("memory"),
      });
    }

    return rows;
  }, [personasPayload, sessions, memory, goToTab, openPersona, patchView]);

  const paletteActions = useMemo<Command[]>(
    () => [
      {
        id: "action-refresh",
        label: "Refresh data",
        hint: "Re-fetch every panel from the active source",
        group: "Actions",
        run: handleRefresh,
      },
      {
        id: "action-demo",
        label: isDemo ? "Use live data" : "Use sample data",
        hint: isDemo
          ? "Stop requesting the demo dataset"
          : "Request the built-in demo dataset instead of the runtime",
        group: "Actions",
        run: () => toggleDemo(!isDemo),
      },
      {
        id: "action-copy-link",
        label: "Copy link to this view",
        hint: "Section, filters and open detail are all in the URL",
        group: "Actions",
        run: handleCopyLink,
      },
      {
        id: "action-shortcuts",
        label: "Keyboard shortcuts",
        hint: "Also on ?",
        group: "Actions",
        run: () => setShortcutsOpen(true),
      },
      {
        id: "action-export-json",
        label: "Export this panel as JSON",
        hint: "Downloads exactly the rows on screen",
        group: "Export",
        run: () => handleExport("json"),
      },
      {
        id: "action-export-csv",
        label: "Export this panel as CSV",
        hint: "Downloads exactly the rows on screen",
        group: "Export",
        run: () => handleExport("csv"),
      },
      ...REFRESH_INTERVALS.filter((seconds) => seconds !== refreshInterval).map((seconds) => ({
        id: `action-interval-${seconds}`,
        label: seconds === 0 ? "Turn auto-refresh off" : `Auto-refresh every ${seconds}s`,
        hint: "Applies to every panel",
        group: "Auto-refresh",
        run: () => setRefreshPref(String(seconds)),
      })),
      ...THEMES.filter((option) => option !== theme).map((option) => ({
        id: `action-theme-${option}`,
        label: option === "system" ? "Theme: match system" : `Theme: ${option}`,
        hint: "Stored per browser",
        group: "Appearance",
        run: () => setTheme(option),
      })),
      {
        id: "action-presenting",
        label: presenting ? "Leave presentation mode" : "Presentation mode",
        hint: "Hide the sidebar and secondary controls for a wall display",
        group: "Actions",
        run: () => setPresenting(!presenting),
      },
      {
        id: "action-print",
        label: "Print this view",
        hint: "Renders the panels on a light background, chrome removed",
        group: "Actions",
        run: () => window.print(),
      },
      ...DENSITIES.filter((option) => option !== density).map((option) => ({
        id: `action-density-${option}`,
        label: `Density: ${option}`,
        hint: "Tightens or relaxes panel spacing",
        group: "Appearance",
        run: () => setDensity(option),
      })),
    ],
    [
      handleRefresh,
      isDemo,
      toggleDemo,
      handleCopyLink,
      handleExport,
      refreshInterval,
      setRefreshPref,
      theme,
      setTheme,
      density,
      setDensity,
      presenting,
      setPresenting,
    ],
  );

  // Only surface a fetched detail when it belongs to the currently selected id.
  const activeSessionDetail =
    sessionId && sessionDetail?.id === sessionId ? sessionDetail.detail : null;
  const activeRunDetail = runId && runDetail?.id === runId ? runDetail.detail : null;

  const counts: Partial<Record<TabId, number>> = {
    overview: personasPayload?.personas.length,
    sessions: sessions?.total,
    memory: memory?.total_facts,
    workflows: workflows?.runs.length,
    audit: audit?.total,
  };

  /** Run counts per persona, for the filter menu's secondary column. */
  const personaRunCounts = useMemo(() => {
    const out: Record<string, number> = {};
    for (const persona of personasPayload?.personas ?? []) out[persona.name] = persona.runs;
    return out;
  }, [personasPayload]);

  const awaitingFirstLoad = isLoading && personasPayload === null && metrics === null;

  return (
    <div className="flex min-h-screen">
      <Sidebar
        active={activeTab}
        onSelect={goToTab}
        collapsed={sidebarCollapsed}
        onCollapsedChange={(next) => setCollapsedPref(next ? "on" : "off")}
        counts={counts}
        mobileOpen={mobileNavOpen}
        onMobileClose={() => setMobileNavOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          active={activeTab}
          isDemo={isDemo}
          onDemoToggle={toggleDemo}
          activeSource={activeSource}
          isLoading={isLoading}
          onRefresh={handleRefresh}
          refreshInterval={refreshInterval}
          onRefreshIntervalChange={(seconds) => setRefreshPref(String(seconds))}
          lastUpdatedAt={lastUpdatedAt}
          now={now}
          onOpenPalette={() => setPaletteOpen(true)}
          onOpenMobileNav={() => setMobileNavOpen(true)}
          theme={theme}
          onThemeChange={setTheme}
          density={density}
          onDensityChange={setDensity}
          presenting={presenting}
          onPresentingChange={setPresenting}
          prefersLight={prefersLight}
          personas={personas}
          onPersonasChange={setPersonas}
          personaCounts={personaRunCounts}
          canExport={exportable !== null && exportable.rows.length > 0}
          onExport={handleExport}
          onCopyLink={handleCopyLink}
        />

        <main
          id="main"
          tabIndex={-1}
          className="mx-auto w-full max-w-[110rem] flex-1 space-y-gap px-4 py-6 focus:outline-none sm:px-6 lg:px-8"
        >
          {/* Announces each completed refresh to a screen reader without
              moving focus or rendering anything. */}
          <p className="sr-only" role="status" aria-live="polite">
            {isLoading
              ? "Loading dashboard data"
              : lastUpdatedAt === null
                ? ""
                : `${navItem(activeTab).label} updated`}
          </p>

          {error && (
            <div
              role="alert"
              className="flex items-start justify-between gap-3 rounded-2xl border border-hue-rose-line bg-hue-rose-tint/40 p-4 text-sm text-hue-rose"
            >
              <span>{error}</span>
              <button
                onClick={() => setError(null)}
                aria-label="Dismiss error"
                className="shrink-0 rounded-lg border border-hue-rose-line px-2 py-0.5 font-mono text-[11px] text-hue-rose hover:bg-hue-rose-tint focus:outline-none focus-visible:ring-2 focus-visible:ring-hue-rose"
              >
                Dismiss
              </button>
            </div>
          )}

          <HostedNotice activeSource={activeSource} isDemo={isDemo} />

          {awaitingFirstLoad ? (
            <KpiSkeleton />
          ) : (
            <KpiStrip
              metrics={metrics}
              memory={memory}
              sessions={sessions}
              audit={audit}
              onNavigate={goToTab}
            />
          )}

          <section key={activeTab} className="animate-panel-in">
            {activeTab === "overview" &&
              (personasPayload ? (
                <AgentOverview
                  personas={personasPayload}
                  selected={personas}
                  onSelect={setPersonas}
                  onOpenDetail={openPersona}
                  trends={metrics?.trends}
                />
              ) : (
                <CardGridSkeleton />
              ))}

            {activeTab === "analytics" &&
              (metrics ? (
                <AnalyticsCharts
                  metrics={metrics}
                  personas={personasPayload ?? undefined}
                  selectedPersonas={personas}
                  trend={trend}
                  onTrendChange={(days) => patchView({ trend: days })}
                />
              ) : (
                <PanelSkeleton label="Loading analytics" />
              ))}

            {activeTab === "sessions" &&
              (sessions ? (
                <SessionExplorer
                  sessions={sessions.sessions}
                  total={sessions.total}
                  search={search}
                  onSearchChange={(value) => patchView({ search: value, page: 1 })}
                  page={page}
                  pageSize={PAGE_SIZE}
                  onPageChange={(next) => patchView({ page: next })}
                  onSessionSelect={(id) => patchView({ session: id })}
                  openSessionId={sessionId}
                  detail={activeSessionDetail}
                  isLoadingDetail={sessionId !== null && activeSessionDetail === null}
                />
              ) : (
                <PanelSkeleton label="Loading sessions" />
              ))}

            {activeTab === "memory" &&
              (memory ? (
                <MemoryExplorer memory={memory} />
              ) : (
                <PanelSkeleton label="Loading memory" />
              ))}

            {activeTab === "workflows" &&
              (workflows ? (
                <WorkflowRuns
                  runs={workflows.runs}
                  familyWide={personas.length > 0}
                  onRunSelect={(id) => patchView({ run: id })}
                  openRunId={runId}
                  detail={activeRunDetail}
                  isLoadingDetail={runId !== null && activeRunDetail === null}
                />
              ) : (
                <PanelSkeleton label="Loading workflow runs" />
              ))}

            {activeTab === "audit" &&
              (audit ? (
                <AuditLogs
                  audit={audit}
                  severity={severity}
                  onSeverityChange={(value) => patchView({ severity: value })}
                />
              ) : (
                <PanelSkeleton label="Loading audit log" />
              ))}

            {/* Static showcase; it reads no runtime data, so it needs no source. */}
            {activeTab === "stitch" && <StitchStudio />}
          </section>

          <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-line-soft pt-4 font-mono text-[11px] text-fg-5">
            <span>
              Read-only. Data from {activeSource ?? "…"}
              {isDemo && " · sample data requested"}
              {personas.length > 0 && ` · filtered to ${personas.length} persona${personas.length === 1 ? "" : "s"}`}
            </span>
            <span className="hidden sm:inline">
              <kbd className="rounded border border-line px-1 py-0.5">⌘K</kbd> commands ·{" "}
              <kbd className="rounded border border-line px-1 py-0.5">?</kbd> shortcuts
            </span>
          </footer>
        </main>
      </div>

      {/* Mounted only while open: the palette's query and highlighted row
          reset by unmounting, with no effect clearing them on the way in. */}
      {paletteOpen && (
        <CommandPalette
          onClose={() => setPaletteOpen(false)}
          onNavigate={goToTab}
          actions={[...paletteActions, ...dataCommands]}
        />
      )}

      {/* Rendered from the page rather than from inside AgentOverview: the
          drawer states each figure as a share of the family, so it needs the
          whole payload, and it stays open across a section change only if the
          page owns it. `goToTab` closes it, which is what the drawer's own
          navigation buttons rely on. */}
      {activePersona && personasPayload && (
        <PersonaDrawer
          persona={activePersona}
          family={personasPayload.personas}
          filtered={personas.includes(activePersona.name)}
          onToggleFilter={() => togglePersona(activePersona.name)}
          onNavigate={goToTab}
          onClose={() => patchView({ agent: null })}
        />
      )}

      {shortcutsOpen && <ShortcutsOverlay onClose={() => setShortcutsOpen(false)} />}

      <ToastStack toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
