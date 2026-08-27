"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";

import AgentOverview from "@/components/AgentOverview";
import AnalyticsCharts from "@/components/AnalyticsCharts";
import AuditLogs from "@/components/AuditLogs";
import CommandPalette, { type Command } from "@/components/CommandPalette";
import HostedNotice from "@/components/HostedNotice";
import KpiStrip from "@/components/KpiStrip";
import MemoryExplorer from "@/components/MemoryExplorer";
import SessionExplorer from "@/components/SessionExplorer";
import Sidebar from "@/components/shell/Sidebar";
import TopBar, { REFRESH_INTERVALS, type RefreshInterval } from "@/components/shell/TopBar";
import { CardGridSkeleton, KpiSkeleton, PanelSkeleton } from "@/components/Skeletons";
import StitchStudio from "@/components/StitchStudio";
import WorkflowRuns from "@/components/WorkflowRuns";
import {
  useDensity,
  useHashRoute,
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
import { isTabId, type TabId } from "@/lib/nav";
import { DENSITIES, THEMES } from "@/lib/theme";

const PAGE_SIZE = 10;

const STORAGE_KEYS = {
  demo: "sak-dashboard:demo",
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
  // Section lives in the URL fragment, so a section is linkable and the back
  // button moves between them.
  const [hash, setHash] = useHashRoute("overview");
  const activeTab: TabId = isTabId(hash) ? hash : "overview";

  const [demoPref, setDemoPref] = usePersistedString(STORAGE_KEYS.demo, "off");
  const isDemo = demoPref === "on";

  const [collapsedPref, setCollapsedPref] = usePersistedString(STORAGE_KEYS.collapsed, "off");
  const sidebarCollapsed = collapsedPref === "on";

  const [refreshPref, setRefreshPref] = usePersistedString(STORAGE_KEYS.refresh, "0");
  const refreshInterval = parseInterval(refreshPref);

  // Appearance. Both are already applied to <html> by the bootstrap script
  // in layout.tsx; these hooks own changing them.
  const [theme, setTheme] = useTheme();
  const [density, setDensity] = useDensity();
  const prefersLight = usePrefersLight();

  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());

  const [personas, setPersonas] = useState<PersonasPayload | null>(null);
  const [metrics, setMetrics] = useState<MetricsPayload | null>(null);
  const [memory, setMemory] = useState<MemoryPayload | null>(null);
  const [audit, setAudit] = useState<AuditPayload | null>(null);
  const [sessions, setSessions] = useState<SessionsPayload | null>(null);
  const [workflows, setWorkflows] = useState<WorkflowsPayload | null>(null);
  const [activeSource, setActiveSource] = useState<DataSource | null>(null);

  // Server-driven query state. These reach the API rather than filtering a
  // client-side copy, so the severity and search parameters the routes have
  // always accepted are finally used.
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [severity, setSeverity] = useState("ALL");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionDetail, setSessionDetail] = useState<{
    id: string;
    detail: SessionDetail | null;
  } | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [runDetail, setRunDetail] = useState<{
    id: string;
    detail: WorkflowRunDetail | null;
  } | null>(null);

  const qs = useCallback(
    (extra: Record<string, string | number | null> = {}) => {
      const params = new URLSearchParams();
      if (isDemo) params.set("demo", "1");
      for (const [key, value] of Object.entries(extra)) {
        if (value !== null && value !== "" && value !== "ALL") params.set(key, String(value));
      }
      const encoded = params.toString();
      return encoded ? `?${encoded}` : "";
    },
    [isDemo],
  );

  // No state is set before the first `await`: the effect below calls this, and
  // a synchronous setState inside an effect schedules a cascading render.
  // The Refresh button sets `isLoading` itself, which is an event handler and
  // therefore fine.
  const refresh = useCallback(async () => {
    const [personasRes, metricsRes, memoryRes, auditRes, sessionsRes, workflowsRes] =
      await Promise.all([
        fetchEnvelope<PersonasPayload>(`/api/agents${qs()}`),
        fetchEnvelope<MetricsPayload>(`/api/metrics${qs()}`),
        fetchEnvelope<MemoryPayload>(`/api/memory${qs()}`),
        fetchEnvelope<AuditPayload>(`/api/audit${qs({ severity })}`),
        fetchEnvelope<SessionsPayload>(
          `/api/sessions${qs({ search, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE })}`,
        ),
        fetchEnvelope<WorkflowsPayload>(`/api/workflows${qs()}`),
      ]);

    if (personasRes) {
      setPersonas(personasRes.data);
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
  }, [qs, search, page, severity]);

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
    void fetchEnvelope<WorkflowRunDetail | null>(`/api/workflows${qs({ id: runId })}`).then(
      (res) => {
        if (!cancelled) setRunDetail({ id: runId, detail: res?.data ?? null });
      },
    );
    return () => {
      cancelled = true;
    };
  }, [runId, qs]);

  const goToTab = useCallback(
    (tab: TabId) => {
      setHash(tab);
    },
    [setHash],
  );

  const handleRefresh = useCallback(() => {
    setIsLoading(true);
    void refresh();
  }, [refresh]);

  const toggleDemo = useCallback(
    (next: boolean) => {
      setDemoPref(next ? "on" : "off");
      setPage(1);
    },
    [setDemoPref],
  );

  // Keyboard: ⌘K/Ctrl+K for the palette, digits for sections, `r` to refresh.
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
      if (event.key === "r") {
        event.preventDefault();
        handleRefresh();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [handleRefresh]);

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
      refreshInterval,
      setRefreshPref,
      theme,
      setTheme,
      density,
      setDensity,
    ],
  );

  // Only surface a fetched detail when it belongs to the currently selected id.
  const activeSessionDetail =
    sessionId && sessionDetail?.id === sessionId ? sessionDetail.detail : null;
  const activeRunDetail = runId && runDetail?.id === runId ? runDetail.detail : null;

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  const counts: Partial<Record<TabId, number>> = {
    overview: personas?.personas.length,
    sessions: sessions?.total,
    memory: memory?.total_facts,
    workflows: workflows?.runs.length,
    audit: audit?.total,
  };

  const awaitingFirstLoad = isLoading && personas === null && metrics === null;

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
          prefersLight={prefersLight}
        />

        <main className="mx-auto w-full max-w-[110rem] flex-1 space-y-6 px-4 py-6 sm:px-6 lg:px-8">
          {error && (
            <div
              role="alert"
              className="flex items-start justify-between gap-3 rounded-2xl border border-hue-rose-line/50 bg-hue-rose-tint/30 p-4 text-sm text-hue-rose"
            >
              <span>{error}</span>
              <button
                onClick={() => setError(null)}
                aria-label="Dismiss error"
                className="shrink-0 rounded-lg border border-hue-rose-line/60 px-2 py-0.5 font-mono text-[11px] text-hue-rose hover:bg-hue-rose-tint/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-hue-rose"
              >
                Dismiss
              </button>
            </div>
          )}

          <HostedNotice activeSource={activeSource} isDemo={isDemo} />

          {awaitingFirstLoad ? <KpiSkeleton /> : (
            <KpiStrip metrics={metrics} memory={memory} sessions={sessions} audit={audit} />
          )}

          <section key={activeTab} className="animate-panel-in">
            {activeTab === "overview" &&
              (personas ? <AgentOverview personas={personas} /> : <CardGridSkeleton />)}

            {activeTab === "analytics" &&
              (metrics ? (
                <AnalyticsCharts metrics={metrics} personas={personas ?? undefined} />
              ) : (
                <PanelSkeleton label="Loading analytics" />
              ))}

            {activeTab === "sessions" &&
              (sessions ? (
                <SessionExplorer
                  sessions={sessions.sessions}
                  total={sessions.total}
                  search={search}
                  onSearchChange={handleSearchChange}
                  page={page}
                  pageSize={PAGE_SIZE}
                  onPageChange={setPage}
                  onSessionSelect={setSessionId}
                  detail={activeSessionDetail}
                  isLoadingDetail={sessionId !== null && activeSessionDetail === null}
                />
              ) : (
                <PanelSkeleton label="Loading sessions" />
              ))}

            {activeTab === "memory" &&
              (memory ? <MemoryExplorer memory={memory} /> : <PanelSkeleton label="Loading memory" />)}

            {activeTab === "workflows" &&
              (workflows ? (
                <WorkflowRuns
                  runs={workflows.runs}
                  onRunSelect={setRunId}
                  detail={activeRunDetail}
                  isLoadingDetail={runId !== null && activeRunDetail === null}
                />
              ) : (
                <PanelSkeleton label="Loading workflow runs" />
              ))}

            {activeTab === "audit" &&
              (audit ? (
                <AuditLogs audit={audit} severity={severity} onSeverityChange={setSeverity} />
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
            </span>
            <span className="hidden sm:inline">
              <kbd className="rounded border border-line px-1 py-0.5">⌘K</kbd> commands ·{" "}
              <kbd className="rounded border border-line px-1 py-0.5">R</kbd> refresh
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
          actions={paletteActions}
        />
      )}
    </div>
  );
}
