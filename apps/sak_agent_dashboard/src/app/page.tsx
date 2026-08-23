"use client";

import { useMemo, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  CircleDot,
  Clock3,
  Command,
  Cpu,
  Database,
  Gauge,
  LayoutDashboard,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Terminal,
  Workflow,
  Zap,
} from "lucide-react";
import DemoModeToggle from "@/components/DemoModeToggle";
import { useDashboardData } from "@/lib/hooks/useDashboardData";
import { TABS, INACTIVE_CLASS, type TabId } from "@/lib/tabs/registry";

const primaryTabs: TabId[] = ["overview", "arena", "analytics", "sessions", "memory"];
const buildTabs: TabId[] = ["workflows", "adk_bridge", "finetune", "benchmarks", "evolution"];
const platformTabs: TabId[] = ["providers", "hub", "skills", "mcp", "gateway", "specs"];

function findTab(id: TabId) {
  return TABS.find((tab) => tab.id === id);
}

export default function Home() {
  const {
    data,
    isLoading,
    isDemo,
    toggleDemo,
    refresh,
    selectedSessionDetail,
    fetchSessionDetail,
  } = useDashboardData();
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  const activeTabDef = TABS.find((tab) => tab.id === activeTab) ?? TABS[0];
  const readyCount = useMemo(
    () => data.agents.filter((agent) => agent.status === "active" || agent.status === "ready").length,
    [data.agents],
  );

  const renderNavGroup = (label: string, ids: TabId[]) => (
    <div className="space-y-2">
      <p className="px-3 text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <div className="space-y-1">
        {ids.map((id) => {
          const tab = findTab(id);
          if (!tab) return null;
          const Icon = tab.icon;
          const isActive = activeTab === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => setActiveTab(id)}
              aria-current={isActive ? "page" : undefined}
              className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/70 ${
                isActive
                  ? "border border-cyan-400/25 bg-cyan-400/10 text-cyan-200 shadow-[0_8px_24px_rgba(34,211,238,0.08)]"
                  : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-100"
              }`}
            >
              <Icon className={`h-4 w-4 shrink-0 ${isActive ? "text-cyan-300" : tab.iconClass}`} />
              <span className="truncate">{tab.label(data).replace(/ \(\d+\)$/, "")}</span>
              {id === "overview" && <span className="ml-auto text-[10px] text-slate-500">{data.agents.length}</span>}
              {id === "arena" && <CircleDot className="ml-auto h-3.5 w-3.5 text-blue-300" />}
            </button>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <div className="flex items-center gap-3 px-2">
          <div className="brand-mark"><span>SAK</span><span className="brand-mark-dot" /></div>
          <div className="min-w-0">
            <p className="truncate font-display text-sm font-semibold tracking-tight text-white">Sak-Agent-Family</p>
            <p className="text-[11px] text-slate-500">Runtime command center</p>
          </div>
        </div>

        <div className="sidebar-search" aria-label="Search workspace">
          <Search className="h-4 w-4 text-slate-500" />
          <span>Search workspace</span>
          <kbd>⌘ K</kbd>
        </div>

        <nav className="mt-7 space-y-6" aria-label="Dashboard navigation">
          {renderNavGroup("Command center", primaryTabs)}
          {renderNavGroup("Build & evaluate", buildTabs)}
          {renderNavGroup("Platform", platformTabs)}
        </nav>

        <div className="mt-auto rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-xs font-medium text-slate-300">System health</span>
            <span className="status-dot bg-emerald-400" />
          </div>
          <div className="mb-2 flex items-end justify-between">
            <span className="font-display text-2xl font-semibold text-white">98.4%</span>
            <span className="text-[11px] text-emerald-300">+2.1%</span>
          </div>
          <div className="health-meter"><span /></div>
          <p className="mt-2 text-[11px] leading-relaxed text-slate-500">All critical services are responding normally.</p>
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-topbar">
          <div>
            <div className="mb-1 flex items-center gap-2 text-xs text-slate-500"><span>Workspace</span><span>/</span><span className="text-slate-300">{activeTabDef.label(data).replace(/ \(\d+\)$/, "")}</span></div>
            <h1 className="font-display text-2xl font-semibold tracking-tight text-white md:text-3xl">Good evening, Sakthai<span className="text-cyan-300">.</span></h1>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="hidden items-center gap-2 rounded-xl border border-white/[0.07] bg-white/[0.03] px-3 py-2 text-xs text-slate-400 lg:flex"><Command className="h-3.5 w-3.5" /><span>Quick actions</span></div>
            <DemoModeToggle isDemo={isDemo} onToggle={toggleDemo} />
            <button type="button" onClick={refresh} disabled={isLoading} aria-label="Refresh telemetry" className="icon-button" title="Refresh telemetry"><RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin text-cyan-300" : ""}`} /></button>
            <div className="avatar">ST</div>
          </div>
        </header>

        {activeTab === "overview" && (
          <section className="hero-panel">
            <div className="hero-orb hero-orb-one" /><div className="hero-orb hero-orb-two" />
            <div className="relative z-10 max-w-2xl">
              <div className="eyebrow"><Sparkles className="h-3.5 w-3.5" /> Live intelligence layer</div>
              <h2 className="mt-5 max-w-xl font-display text-3xl font-semibold leading-tight tracking-tight text-white md:text-5xl">Orchestrate every agent from one <span className="gradient-text">clear view.</span></h2>
              <p className="mt-4 max-w-lg text-sm leading-7 text-slate-400">Monitor persona health, inspect memory, compare model quality, and move from signal to action without leaving the runtime.</p>
              <div className="mt-7 flex flex-wrap gap-3"><button type="button" onClick={() => setActiveTab("arena")} className="primary-button"><Zap className="h-4 w-4" /> Open Chat Arena <ArrowUpRight className="h-4 w-4" /></button><button type="button" onClick={() => setActiveTab("analytics")} className="secondary-button"><Gauge className="h-4 w-4" /> View analytics</button></div>
            </div>
            <div className="hero-signal-card"><div className="flex items-center justify-between"><span className="text-xs text-slate-400">Runtime pulse</span><span className="live-pill"><span className="status-dot bg-emerald-400" /> Live</span></div><div className="mt-7 flex items-end gap-2"><span className="font-display text-5xl font-semibold text-white">{data.metrics.totalRuns ?? data.totalSessions ?? 0}</span><span className="mb-2 text-xs text-emerald-300">runs today</span></div><div className="signal-bars mt-5"><span /><span /><span /><span /><span /><span /><span /><span /><span /><span /><span /><span /></div><div className="mt-3 flex justify-between text-[10px] text-slate-500"><span>00:00</span><span>Now</span></div></div>
          </section>
        )}

        <section className="metric-grid" aria-label="Runtime summary">
          <div className="metric-card"><div className="metric-icon cyan"><Activity /></div><div><p className="metric-label">Total runs</p><p className="metric-value">{data.metrics.totalRuns ?? data.totalSessions ?? 0}</p><p className="metric-change positive">+12.8% <span>vs last week</span></p></div></div>
          <div className="metric-card"><div className="metric-icon violet"><Bot /></div><div><p className="metric-label">Active personas</p><p className="metric-value">{readyCount || data.agents.length}</p><p className="metric-change"><span>of {data.agents.length} registered</span></p></div></div>
          <div className="metric-card"><div className="metric-icon emerald"><Database /></div><div><p className="metric-label">Memory index</p><p className="metric-value">{(data.memory?.facts.length ?? 0) + (data.memory?.observations.length ?? 0)}<span className="metric-suffix"> docs</span></p><p className="metric-change positive"><CheckCircle2 className="inline h-3 w-3" /> synchronized</p></div></div>
          <div className="metric-card"><div className="metric-icon amber"><ShieldCheck /></div><div><p className="metric-label">Security posture</p><p className="metric-value">A<span className="metric-suffix">+ grade</span></p><p className="metric-change positive">All checks passing</p></div></div>
        </section>

        <div className="workspace-strip"><div className="flex items-center gap-2"><Terminal className="h-4 w-4 text-cyan-300" /><span className="text-sm font-medium text-slate-200">{activeTabDef.label(data).replace(/ \(\d+\)$/, "")}</span><span className="hidden text-xs text-slate-500 sm:inline">/ workspace view</span></div><div className="flex items-center gap-3 text-xs text-slate-500"><span className="hidden items-center gap-1.5 sm:flex"><Clock3 className="h-3.5 w-3.5" /> Updated just now</span><span className="flex items-center gap-1.5"><Workflow className="h-3.5 w-3.5 text-cyan-300" /> {isDemo ? "Demo data" : "Live data"}</span></div></div>

        <div className="dashboard-content">
          {activeTabDef.render(data, { onSessionSelect: fetchSessionDetail, selectedSessionDetail })}
        </div>
      </main>
    </div>
  );
}
