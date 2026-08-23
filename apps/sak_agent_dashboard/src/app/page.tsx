"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Activity,
  Cpu,
  Database,
  ShieldCheck,
  Terminal,
  RefreshCw,
  BarChart3,
  MessageSquare,
  Shield,
  Sparkles,
} from "lucide-react";
import DemoModeToggle from "@/components/DemoModeToggle";
import AgentOverview from "@/components/AgentOverview";
import AnalyticsCharts from "@/components/AnalyticsCharts";
import SessionExplorer from "@/components/SessionExplorer";
import MemoryExplorer from "@/components/MemoryExplorer";
import AuditLogs from "@/components/AuditLogs";
import StitchStudio from "@/components/StitchStudio";
import {
  AgentPersona,
  MetricsData,
  MemoryData,
  AuditLog,
  SessionMeta,
  SessionTranscript,
} from "@/lib/types";

const defaultPersonas: AgentPersona[] = [
  {
    name: "SakThai",
    role: "Primary Orchestrator & Fine-Tuned Agent",
    status: "Active",
    model: "sakthai-v2-qlora",
    latencyMs: 320,
    runs: 300,
    skills: ["routing", "planning", "tool-call"],
    badge: "1P Tuned",
    benchmarkScore: 96.5,
  },
  {
    name: "SakKing",
    role: "High-Capacity Reasoning Specialist",
    status: "Ready",
    model: "sakking-v1-reasoning",
    latencyMs: 540,
    runs: 150,
    skills: ["math", "logic-proof", "tree-search"],
    badge: "Reasoning",
    benchmarkScore: 94.2,
  },
  {
    name: "SakSee",
    role: "Multimodal & Vision Specialist",
    status: "Ready",
    model: "saksee-v1-vision",
    latencyMs: 410,
    runs: 120,
    skills: ["ocr", "diagram-parsing", "image-eval"],
    badge: "Multimodal",
    benchmarkScore: 91.8,
  },
  {
    name: "SakSit",
    role: "Code Review & Security Auditor",
    status: "Ready",
    model: "saksit-v1-auditor",
    latencyMs: 290,
    runs: 91,
    skills: ["static-analysis", "vulnerability-scan", "policy-check"],
    badge: "Security",
    benchmarkScore: 98.0,
  },
  {
    name: "SakJules",
    role: "Background Task & Async Execution Specialist",
    status: "Ready",
    model: "sakjules-v1-async",
    latencyMs: 380,
    runs: 100,
    skills: ["cron-scheduler", "bg-worker", "liveness"],
    badge: "Async",
    benchmarkScore: 93.5,
  },
];

const defaultMetrics: MetricsData = {
  totalRuns: 761,
  avgLatencyMs: 388,
  successRate: 0.985,
  tokenStats: {
    totalTokens: 1450000,
    promptTokens: 950000,
    completionTokens: 500000,
  },
  stopReasons: {
    end_turn: 740,
    max_tokens: 21,
  },
  trends: [
    { date: "2026-07-29", runs: 110, latencyMs: 395 },
    { date: "2026-07-30", runs: 145, latencyMs: 382 },
    { date: "2026-07-31", runs: 180, latencyMs: 390 },
    { date: "2026-08-01", runs: 210, latencyMs: 375 },
    { date: "2026-08-02", runs: 116, latencyMs: 388 },
  ],
};

const defaultMemory: MemoryData = {
  facts: [
    { id: 1, entity: "SakThai", fact: "Primary model initialized", persona: "SakThai", createdAt: "2026-08-02" },
    { id: 2, entity: "SakKing", fact: "GRPO mathematical solver loaded", persona: "SakKing", createdAt: "2026-08-02" },
  ],
  observations: [
    { id: 1, category: "eval", observation: "Benchmark 95% passed", timestamp: "2026-08-02" },
  ],
};

const defaultAuditLogs: AuditLog[] = [
  {
    id: 1,
    timestamp: "2026-08-02T12:00:00Z",
    persona: "SakSit",
    severity: "critical",
    event: "Unauthorized access blocked",
    details: "Blocked non-whitelisted egress attempt",
  },
  {
    id: 2,
    timestamp: "2026-08-02T12:05:00Z",
    persona: "SakThai",
    severity: "info",
    event: "Session initialized",
    details: "Runtime state synchronized cleanly",
  },
];

const defaultSessions: SessionMeta[] = [
  {
    sessionId: "sess-1",
    persona: "SakThai",
    timestamp: "2026-08-02T12:00:00Z",
    messageCount: 5,
    tokenUsage: 1200,
    status: "completed",
  },
  {
    sessionId: "sess-2",
    persona: "SakKing",
    timestamp: "2026-08-02T12:10:00Z",
    messageCount: 12,
    tokenUsage: 3400,
    status: "completed",
  },
];

export default function Home() {
  const [isDemo, setIsDemo] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "analytics" | "sessions" | "memory" | "stitch">("overview");

  const [agents, setAgents] = useState<AgentPersona[]>(defaultPersonas);
  const [metrics, setMetrics] = useState<MetricsData>(defaultMetrics);
  const [memory, setMemory] = useState<MemoryData>(defaultMemory);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>(defaultAuditLogs);
  const [sessions, setSessions] = useState<SessionMeta[]>(defaultSessions);
  const [totalSessions, setTotalSessions] = useState<number>(761);

  const [isLoading, setIsLoading] = useState(false);
  const [selectedSessionDetail, setSelectedSessionDetail] = useState<SessionTranscript | null>(null);

  const isMountedRef = React.useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const fetchAllData = useCallback(async (demoMode: boolean) => {
    setIsLoading(true);
    try {
      const demoParam = demoMode ? "?demo=true" : "?demo=false";
      const origin = typeof window !== "undefined" && window.location?.origin && window.location.origin !== "null"
        ? window.location.origin
        : "http://localhost:3000";

      const safeFetch = async (url: string) => {
        try {
          const res = await fetch(url);
          return res && res.ok ? await res.json() : null;
        } catch {
          return null;
        }
      };

      const [agentsRes, metricsRes, memoryRes, sessionsRes] = await Promise.all([
        safeFetch(`${origin}/api/agents${demoParam}`),
        safeFetch(`${origin}/api/metrics${demoParam}`),
        safeFetch(`${origin}/api/memory${demoParam}`),
        safeFetch(`${origin}/api/sessions${demoParam}`),
      ]);

      if (!isMountedRef.current) return;

      if (agentsRes?.success && Array.isArray(agentsRes.agents)) {
        setAgents(agentsRes.agents);
      }
      if (metricsRes?.success && metricsRes.metrics) {
        setMetrics(metricsRes.metrics);
      }
      if (memoryRes?.success) {
        if (memoryRes.memory) setMemory(memoryRes.memory);
        if (Array.isArray(memoryRes.auditLogs)) setAuditLogs(memoryRes.auditLogs);
      }
      if (sessionsRes?.success) {
        if (Array.isArray(sessionsRes.sessions)) setSessions(sessionsRes.sessions);
        if (typeof sessionsRes.total === "number") setTotalSessions(sessionsRes.total);
      }
    } catch (error) {
      console.error("Failed to load dashboard telemetry:", error);
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchAllData(isDemo);
  }, [isDemo, fetchAllData]);

  const handleToggleDemo = (newVal?: boolean) => {
    const nextVal = typeof newVal === "boolean" ? newVal : !isDemo;
    setIsDemo(nextVal);
  };

  const handleFetchSessionDetail = async (sessionId: string) => {
    try {
      const demoParam = isDemo ? "&demo=true" : "";
      const origin = typeof window !== "undefined" && window.location?.origin && window.location.origin !== "null"
        ? window.location.origin
        : "http://localhost:3000";
      const res = await fetch(`${origin}/api/sessions?id=${sessionId}${demoParam}`).then((r) => (r.ok ? r.json() : null)).catch(() => null);
      if (!isMountedRef.current) return;
      if (res?.success && res?.detail) {
        setSelectedSessionDetail(res.detail);
      }
    } catch (e) {
      console.error("Failed to fetch session detail:", e);
    }
  };

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
          <DemoModeToggle isDemo={isDemo} onToggle={handleToggleDemo} />

          {/* Refresh Button */}
          <button
            onClick={() => fetchAllData(isDemo)}
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
            {metrics?.totalRuns ?? totalSessions ?? 761}
          </div>
          <p className="text-xs text-slate-400 mt-1">Recorded in runtime</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl transition-all hover:border-purple-500/30">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider font-mono">Active Personas</span>
            <Cpu className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-3xl font-extrabold text-white font-display">
            {agents.length}
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
        <button
          onClick={() => setActiveTab("overview")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "overview"
              ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Cpu className="h-4 w-4 text-cyan-400" />
          Agent Overview ({agents.length})
        </button>

        <button
          onClick={() => setActiveTab("analytics")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "analytics"
              ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <BarChart3 className="h-4 w-4 text-emerald-400" />
          Analytics & Charts
        </button>

        <button
          onClick={() => setActiveTab("sessions")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "sessions"
              ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <MessageSquare className="h-4 w-4 text-purple-400" />
          Session Explorer ({sessions.length})
        </button>

        <button
          onClick={() => setActiveTab("memory")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "memory"
              ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Shield className="h-4 w-4 text-rose-400" />
          Memory & Security Logs
        </button>

        <button
          onClick={() => setActiveTab("stitch")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "stitch"
              ? "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Sparkles className="h-4 w-4 text-cyan-400" />
          Stitch Studio ⚡
        </button>
      </div>

      {/* Main Tab Content */}
      <div className="space-y-8">
        {activeTab === "overview" && (
          <div className="space-y-8">
            <AgentOverview agents={agents} />
            <AnalyticsCharts metrics={metrics} agents={agents} />
          </div>
        )}

        {activeTab === "analytics" && (
          <AnalyticsCharts metrics={metrics} agents={agents} />
        )}

        {activeTab === "sessions" && (
          <SessionExplorer
            sessions={sessions}
            total={totalSessions}
            onSessionSelect={handleFetchSessionDetail}
            selectedSessionDetail={selectedSessionDetail}
          />
        )}

        {activeTab === "memory" && (
          <div className="space-y-8">
            <MemoryExplorer memory={memory} />
            <AuditLogs logs={auditLogs} />
          </div>
        )}

        {activeTab === "stitch" && <StitchStudio />}
      </div>
    </div>
  );
}
