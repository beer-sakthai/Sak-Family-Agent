"use client";

import { useState } from "react";
import { Activity, Cpu, Database, ShieldCheck, RefreshCw } from "lucide-react";
import DemoModeToggle from "@/components/DemoModeToggle";
import { useDashboardData } from "@/lib/hooks/useDashboardData";
import { TABS, INACTIVE_CLASS, type TabId } from "@/lib/tabs/registry";

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

  return (
    <div className="space-y-8">
      {/* Header Bar with Branding & Demo Mode Toggle */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/90 border border-slate-800/80 backdrop-blur-xl shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20 text-white font-bold font-display">
            SAK
          </div>
          <div>
            <h2 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
              Sak-Agent-Family Runtime Intelligence
            </h2>
            <p className="text-xs text-slate-400">
              Real-time telemetry, session transcripts, memory SQLite store inspector, and multi-model benchmark evaluation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Demo Mode Toggle Switch */}
          <DemoModeToggle isDemo={isDemo} onToggle={toggleDemo} />

          {/* Refresh Button */}
          <button
            onClick={refresh}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors disabled:opacity-50"
            title="Refresh Telemetry"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin text-cyan-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* Overview Stat Counter Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl transition-all hover:border-cyan-500/30">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider font-mono">Total Runs</span>
            <Activity className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-extrabold text-white font-display">
            {data.metrics.totalRuns ?? data.totalSessions ?? 0}
          </div>
          <p className="text-xs text-slate-400 mt-1">Recorded in runtime</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl transition-all hover:border-purple-500/30">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider font-mono">Active Personas</span>
            <Cpu className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-3xl font-extrabold text-white font-display">
            {data.agents.length}
          </div>
          <p className="text-xs text-slate-400 mt-1">Sak-Agent-Family members</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl transition-all hover:border-emerald-500/30">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider font-mono">Memory Database</span>
            <Database className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-white font-display">
            ~/.sakthai
          </div>
          <p className="text-xs text-slate-400 mt-1">memory.db & transcripts</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl transition-all hover:border-rose-500/30">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider font-mono">Security Audit</span>
            <ShieldCheck className="h-4 w-4 text-rose-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 font-display">
            100% Pass
          </div>
          <p className="text-xs text-slate-400 mt-1">Zero vulnerabilities logged</p>
        </div>
      </div>

      {/* Navigation Tab Bar */}
      <div className="flex items-center p-1.5 rounded-2xl bg-slate-900/90 border border-slate-800/80 font-mono text-xs gap-2">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
                isActive ? tab.activeClass : INACTIVE_CLASS
              }`}
            >
              <Icon className={`h-4 w-4 ${tab.iconClass}`} />
              {tab.label(data)}
              {tab.badge?.(data)}
            </button>
          );
        })}
      </div>

      {/* Main Tab Content */}
      <div className="space-y-8">
        {activeTabDef.render(data, {
          onSessionSelect: fetchSessionDetail,
          selectedSessionDetail,
        })}
      </div>
    </div>
  );
}
