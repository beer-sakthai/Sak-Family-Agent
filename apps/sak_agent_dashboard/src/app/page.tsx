"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Activity,
  BarChart3,
  Database,
  GitBranch,
  MessageSquare,
  RefreshCw,
  Shield,
  Terminal,
} from "lucide-react";

import AgentOverview from "@/components/AgentOverview";
import AnalyticsCharts from "@/components/AnalyticsCharts";
import AuditLogs from "@/components/AuditLogs";
import DemoModeToggle from "@/components/DemoModeToggle";
import MemoryExplorer from "@/components/MemoryExplorer";
import SessionExplorer from "@/components/SessionExplorer";
import WorkflowRuns from "@/components/WorkflowRuns";
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

type Tab = "overview" | "analytics" | "sessions" | "memory" | "workflows" | "audit";

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: "overview", label: "Overview", icon: <Activity className="h-3.5 w-3.5" /> },
  { id: "analytics", label: "Analytics", icon: <BarChart3 className="h-3.5 w-3.5" /> },
  { id: "sessions", label: "Sessions", icon: <MessageSquare className="h-3.5 w-3.5" /> },
  { id: "memory", label: "Memory", icon: <Database className="h-3.5 w-3.5" /> },
  { id: "workflows", label: "Workflows", icon: <GitBranch className="h-3.5 w-3.5" /> },
  { id: "audit", label: "Audit", icon: <Shield className="h-3.5 w-3.5" /> },
];

const PAGE_SIZE = 10;

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

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [isDemo, setIsDemo] = useState(false);
  const [activeSource, setActiveSource] = useState<DataSource | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [personas, setPersonas] = useState<PersonasPayload | null>(null);
  const [metrics, setMetrics] = useState<MetricsPayload | null>(null);
  const [memory, setMemory] = useState<MemoryPayload | null>(null);
  const [audit, setAudit] = useState<AuditPayload | null>(null);
  const [sessions, setSessions] = useState<SessionsPayload | null>(null);
  const [workflows, setWorkflows] = useState<WorkflowsPayload | null>(null);

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

  const demoParam = isDemo ? "demo=1" : "";
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
    setIsLoading(false);
  }, [qs, search, page, severity]);

  useEffect(() => {
    // refresh() sets no state before its first `await`, so nothing here runs
    // synchronously; the rule cannot see through the useCallback to tell.
    // Fetching on mount is the intended use of an effect.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

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

  // Only surface a fetched detail when it belongs to the currently selected id.
  const activeSessionDetail = sessionId && sessionDetail?.id === sessionId
    ? sessionDetail.detail
    : null;
  const activeRunDetail = runId && runDetail?.id === runId ? runDetail.detail : null;

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  const handleSeverityChange = (value: string) => {
    setSeverity(value);
  };

  return (
    <main className="min-h-screen px-4 sm:px-6 lg:px-10 py-8 space-y-8 max-w-[100rem] mx-auto">
      <header className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-2xl bg-slate-900 border border-slate-800">
            <Terminal className="h-6 w-6 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-display text-white tracking-tight">
              Sak-Agent-Family Dashboard
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Agents, workflows, memory, and security across the family
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <DemoModeToggle
            isDemo={isDemo}
            onToggle={(next) => {
              setIsDemo(next);
              setPage(1);
            }}
            activeSource={activeSource}
          />
          <button
            onClick={() => {
              setIsLoading(true);
              void refresh();
            }}
            disabled={isLoading}
            aria-label="Refresh dashboard data"
            className="px-3 py-1.5 rounded-xl text-[11px] font-mono bg-slate-900/60 text-slate-300 border border-slate-800 hover:border-slate-700 disabled:opacity-50 transition-colors inline-flex items-center gap-1.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
          >
            <RefreshCw className={`h-3 w-3 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </header>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-800/50 text-rose-200 text-sm">
          {error}
        </div>
      )}

      <nav role="tablist" aria-label="Dashboard sections" className="flex flex-wrap gap-2">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-xl text-xs font-mono border transition-colors inline-flex items-center gap-1.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
              activeTab === tab.id
                ? "bg-cyan-950/50 text-cyan-300 border-cyan-700/50"
                : "bg-slate-900/60 text-slate-400 border-slate-800 hover:border-slate-700"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </nav>

      <section>
        {activeTab === "overview" && personas && <AgentOverview personas={personas} />}
        {activeTab === "analytics" && metrics && (
          <AnalyticsCharts metrics={metrics} personas={personas ?? undefined} />
        )}
        {activeTab === "sessions" && sessions && (
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
        )}
        {activeTab === "memory" && memory && <MemoryExplorer memory={memory} />}
        {activeTab === "workflows" && workflows && (
          <WorkflowRuns
            runs={workflows.runs}
            onRunSelect={setRunId}
            detail={activeRunDetail}
            isLoadingDetail={runId !== null && activeRunDetail === null}
          />
        )}
        {activeTab === "audit" && audit && (
          <AuditLogs
            audit={audit}
            severity={severity}
            onSeverityChange={handleSeverityChange}
          />
        )}

        {isLoading && !personas && (
          <p className="text-sm text-slate-500 font-mono py-12 text-center">Loading…</p>
        )}
      </section>

      <footer className="text-[11px] font-mono text-slate-600 pt-4 border-t border-slate-900">
        Read-only. Data from {activeSource ?? "…"}
        {demoParam && " · sample data"}
      </footer>
    </main>
  );
}
