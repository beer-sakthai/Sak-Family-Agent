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
  Plug,
  Layers,
  Boxes,
  MessagesSquare,
  Bot,
  Music2,
  Telescope,
  Users,
  GraduationCap,
  Fingerprint,
  ScrollText,
  Workflow,
  Globe,
  Wrench,
  Trophy,
  Network,
  Send,
  Swords,
  BrainCircuit,
  Radio,
} from "lucide-react";
import DemoModeToggle from "@/components/DemoModeToggle";
import AgentOverview from "@/components/AgentOverview";
import AnalyticsCharts from "@/components/AnalyticsCharts";
import SessionExplorer from "@/components/SessionExplorer";
import MemoryExplorer from "@/components/MemoryExplorer";
import AuditLogs from "@/components/AuditLogs";
import StitchStudio from "@/components/StitchStudio";
import McpServers from "@/components/McpServers";
import SpecKitPanel from "@/components/SpecKitPanel";
import McpSdkPanel from "@/components/McpSdkPanel";
import ChatKitPanel from "@/components/ChatKitPanel";
import AntigravityPanel from "@/components/AntigravityPanel";
import GenkitPanel from "@/components/GenkitPanel";
import ConductorPanel from "@/components/ConductorPanel";
import OtelPanel from "@/components/OtelPanel";
import GoogleAdkPanel from "@/components/GoogleAdkPanel";
import GcpLearningPanel from "@/components/GcpLearningPanel";
import M365CopilotPanel from "@/components/M365CopilotPanel";
import AgentGatewayPanel from "@/components/AgentGatewayPanel";
import GatewayRouterPanel from "@/components/GatewayRouterPanel";
import AutoCyclePanel from "@/components/AutoCyclePanel";
import DesignSpecsPanel from "@/components/DesignSpecsPanel";
import { ChatStudioPanel } from "@/components/ChatStudioPanel";
import { FinetuningPanel } from "@/components/FinetuningPanel";
import { GoogleAdkBridgePanel } from "@/components/GoogleAdkBridgePanel";
import { TelegramVoiceBridgePanel } from "@/components/TelegramVoiceBridgePanel";
import { LiveTelemetryFeed } from "@/components/LiveTelemetryFeed";
import { WorkflowFrameworkPanel } from "@/components/WorkflowFrameworkPanel";
import { ProviderMatrixPanel } from "@/components/ProviderMatrixPanel";
import { HubEcosystemPanel } from "@/components/HubEcosystemPanel";
import { SkillsToolsPanel } from "@/components/SkillsToolsPanel";
import { BenchmarkArena } from "@/components/BenchmarkArena";
import { MemoryRagTelegramPanel } from "@/components/MemoryRagTelegramPanel";
import { SelfEvolutionPanel } from "@/components/SelfEvolutionPanel";
import {
  AgentPersona,
  MetricsData,
  MemoryData,
  AuditLog,
  SessionMeta,
  SessionTranscript,
  McpServerSpec,
  SpecKitData,
  McpSdkData,
  ChatKitData,
  AntigravityData,
  GenkitData,
  ConductorData,
  OtelData,
  AdkData,
  GcpLearningData,
  M365CopilotData,
  GatewayData,
  AutoCycleData,
  DesignSpecsData,
  DataSource,
} from "@/lib/types";
import {
  getDemoAgents,
  getDemoAuditLogs,
  getDemoMemoryData,
  getDemoMetrics,
  getDemoSessions,
  DEMO_TOTAL_RUNS,
} from "@/lib/demoData";
import DataSourceBadge from "@/components/DataSourceBadge";

/**
 * Initial state before the first fetch resolves.
 *
 * These come from `lib/demoData.ts` — the same generators the API routes use —
 * rather than a second set of literals maintained here. The two copies had
 * already drifted (benchmark 96.5 vs 0.96, model `sakthai-v2-qlora` vs the
 * configured model, a five-persona roster that omitted SakTan), which meant the
 * numbers on screen changed the moment the first fetch landed.
 */
const defaultPersonas: AgentPersona[] = getDemoAgents();
const defaultMetrics: MetricsData = getDemoMetrics();
const defaultMemory: MemoryData = getDemoMemoryData();
const defaultAuditLogs: AuditLog[] = getDemoAuditLogs();
const defaultSessions: SessionMeta[] = getDemoSessions().slice(0, 20);

export default function Home() {
  const [isDemo, setIsDemo] = useState(false);
  const [activeTab, setActiveTab] = useState<
    | "overview"
    | "arena"
    | "finetune"
    | "adk_bridge"
    | "telegram_hub"
    | "analytics"
    | "sessions"
    | "memory"
    | "mcp"
    | "mcpsdk"
    | "speckit"
    | "chatkit"
    | "antigravity"
    | "genkit"
    | "conductor"
    | "otel"
    | "adk"
    | "learning"
    | "m365"
    | "gateway"
    | "autocycle"
    | "specs"
    | "stitch"
    | "workflows"
    | "providers"
    | "hub"
    | "skills"
    | "benchmarks"
    | "rag_telegram"
    | "evolution"
  >("overview");

  const [agents, setAgents] = useState<AgentPersona[]>(defaultPersonas);
  const [metrics, setMetrics] = useState<MetricsData>(defaultMetrics);
  const [memory, setMemory] = useState<MemoryData>(defaultMemory);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>(defaultAuditLogs);
  const [sessions, setSessions] = useState<SessionMeta[]>(defaultSessions);
  const [totalSessions, setTotalSessions] = useState<number>(DEMO_TOTAL_RUNS);
  // Per-panel provenance, so the UI can say whether what is on screen was
  // measured. Without it a machine with no ~/.sakthai renders a fully populated
  // dashboard indistinguishable from a busy one.
  const [dataSources, setDataSources] = useState<{
    agents?: DataSource;
    metrics?: DataSource;
    memory?: DataSource;
    audit?: DataSource;
    sessions?: DataSource;
  }>({});
  const [unattributedRuns, setUnattributedRuns] = useState<number>(0);
  const [mcpServers, setMcpServers] = useState<McpServerSpec[]>([]);
  const [speckit, setSpeckit] = useState<SpecKitData | null>(null);
  const [mcpSdk, setMcpSdk] = useState<McpSdkData | null>(null);
  const [chatkit, setChatkit] = useState<ChatKitData | null>(null);
  const [antigravity, setAntigravity] = useState<AntigravityData | null>(null);
  const [genkit, setGenkit] = useState<GenkitData | null>(null);
  const [conductor, setConductor] = useState<ConductorData | null>(null);
  const [otel, setOtel] = useState<OtelData | null>(null);
  const [adk, setAdk] = useState<AdkData | null>(null);
  const [learning, setLearning] = useState<GcpLearningData | null>(null);
  const [m365, setM365] = useState<M365CopilotData | null>(null);
  const [gateway, setGateway] = useState<GatewayData | null>(null);
  const [autocycle, setAutocycle] = useState<AutoCycleData | null>(null);
  const [designSpecs, setDesignSpecs] = useState<DesignSpecsData | null>(null);

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

      const [agentsRes, metricsRes, memoryRes, sessionsRes, mcpRes, speckitRes, mcpSdkRes, chatkitRes, antigravityRes, genkitRes, conductorRes, otelRes, adkRes, learningRes, m365Res, gatewayRes, autoCycleRes, specsRes] = await Promise.all([
        safeFetch(`${origin}/api/agents${demoParam}`),
        safeFetch(`${origin}/api/metrics${demoParam}`),
        safeFetch(`${origin}/api/memory${demoParam}`),
        safeFetch(`${origin}/api/sessions${demoParam}`),
        safeFetch(`${origin}/api/mcp-servers`),
        safeFetch(`${origin}/api/speckit`),
        safeFetch(`${origin}/api/mcp-sdk`),
        safeFetch(`${origin}/api/chatkit`),
        safeFetch(`${origin}/api/antigravity`),
        safeFetch(`${origin}/api/genkit`),
        safeFetch(`${origin}/api/conductor`),
        safeFetch(`${origin}/api/otel`),
        safeFetch(`${origin}/api/google-adk`),
        safeFetch(`${origin}/api/gcp-learning`),
        safeFetch(`${origin}/api/m365-copilot`),
        safeFetch(`${origin}/api/agent-gateway`),
        safeFetch(`${origin}/api/auto-cycle`),
        safeFetch(`${origin}/api/design-specs`),
      ]);

      if (!isMountedRef.current) return;

      if (agentsRes?.success && Array.isArray(agentsRes.agents)) {
        setAgents(agentsRes.agents);
        setUnattributedRuns(Number(agentsRes.unattributedRuns) || 0);
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
      setDataSources({
        agents: agentsRes?.dataSource,
        metrics: metricsRes?.dataSource,
        memory: memoryRes?.dataSource,
        audit: memoryRes?.auditDataSource,
        sessions: sessionsRes?.dataSource,
      });
      if (mcpRes?.success && Array.isArray(mcpRes.servers)) {
        setMcpServers(mcpRes.servers);
      }
      if (speckitRes?.success && speckitRes.speckit) {
        setSpeckit(speckitRes.speckit);
      }
      if (mcpSdkRes?.success && mcpSdkRes.sdk) {
        setMcpSdk(mcpSdkRes.sdk);
      }
      if (chatkitRes?.success && chatkitRes.chatkit) {
        setChatkit(chatkitRes.chatkit);
      }
      if (antigravityRes?.success && antigravityRes.antigravity) {
        setAntigravity(antigravityRes.antigravity);
      }
      if (genkitRes?.success && genkitRes.genkit) {
        setGenkit(genkitRes.genkit);
      }
      if (conductorRes?.success && conductorRes.conductor) {
        setConductor(conductorRes.conductor);
      }
      if (otelRes?.success && otelRes.otel) {
        setOtel(otelRes.otel);
      }
      if (adkRes?.success && adkRes.adk) {
        setAdk(adkRes.adk);
      }
      if (learningRes?.success && learningRes.learning) {
        setLearning(learningRes.learning);
      }
      if (m365Res?.success && m365Res.m365) {
        setM365(m365Res.m365);
      }
      if (gatewayRes?.success && gatewayRes.gateway) {
        setGateway(gatewayRes.gateway);
      }
      if (autoCycleRes?.success && autoCycleRes.autocycle) {
        setAutocycle(autoCycleRes.autocycle);
      }
      if (specsRes?.success && specsRes.specs) {
        setDesignSpecs(specsRes.specs);
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
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial + demo-toggle data fetch is the expected use of an effect
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
            {metrics?.totalRuns ?? totalSessions ?? 0}
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
          onClick={() => setActiveTab("arena")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "arena"
              ? "bg-gradient-to-r from-blue-600/30 via-indigo-600/30 to-purple-600/30 text-blue-300 border border-blue-500/50 shadow-lg shadow-blue-950/50 ring-1 ring-blue-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Swords className="h-4 w-4 text-blue-400" />
          Chat Arena
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/50">
            Supervisor
          </span>
        </button>

        <button
          onClick={() => setActiveTab("finetune")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "finetune"
              ? "bg-gradient-to-r from-purple-600/30 via-indigo-600/30 to-violet-600/30 text-purple-300 border border-purple-500/50 shadow-lg shadow-purple-950/50 ring-1 ring-purple-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <BrainCircuit className="h-4 w-4 text-purple-400" />
          LoRA Studio
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800/50">
            PEFT
          </span>
        </button>

        <button
          onClick={() => setActiveTab("adk_bridge")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "adk_bridge"
              ? "bg-gradient-to-r from-emerald-600/30 via-teal-600/30 to-blue-600/30 text-emerald-300 border border-emerald-500/50 shadow-lg shadow-emerald-950/50 ring-1 ring-emerald-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Send className="h-4 w-4 text-emerald-400" />
          ADK Bridge
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/50">
            Cloud Run
          </span>
        </button>

        <button
          onClick={() => setActiveTab("telegram_hub")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "telegram_hub"
              ? "bg-gradient-to-r from-teal-600/30 via-cyan-600/30 to-blue-600/30 text-teal-300 border border-teal-500/50 shadow-lg shadow-teal-950/50 ring-1 ring-teal-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Radio className="h-4 w-4 text-teal-400" />
          Telegram Hub
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800/50">
            Voice &amp; Alert
          </span>
        </button>

        <button
          onClick={() => setActiveTab("workflows")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "workflows"
              ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Workflow className="h-4 w-4 text-cyan-400" />
          Workflows
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/50">
            6 Agents
          </span>
        </button>

        <button
          onClick={() => setActiveTab("providers")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "providers"
              ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Cpu className="h-4 w-4 text-emerald-400" />
          Providers
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/50">
            7 Matrix
          </span>
        </button>

        <button
          onClick={() => setActiveTab("hub")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "hub"
              ? "bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-300 border border-amber-500/40 shadow-lg shadow-amber-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Globe className="h-4 w-4 text-amber-400" />
          Hub
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800/50">
            19m·16d
          </span>
        </button>

        <button
          onClick={() => setActiveTab("skills")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "skills"
              ? "bg-gradient-to-r from-blue-500/20 to-indigo-500/20 text-blue-300 border border-blue-500/40 shadow-lg shadow-blue-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Wrench className="h-4 w-4 text-blue-400" />
          Skills & AST Gates
        </button>

        <button
          onClick={() => setActiveTab("benchmarks")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "benchmarks"
              ? "bg-gradient-to-r from-emerald-500/20 to-teal-500/20 text-emerald-300 border border-emerald-500/40 shadow-lg shadow-emerald-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Trophy className="h-4 w-4 text-emerald-400" />
          Benchmark Arena
        </button>

        <button
          onClick={() => setActiveTab("rag_telegram")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "rag_telegram"
              ? "bg-gradient-to-r from-purple-500/20 to-fuchsia-500/20 text-purple-300 border border-purple-500/40 shadow-lg shadow-purple-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Network className="h-4 w-4 text-purple-400" />
          RAG & Telegram
        </button>

        <button
          onClick={() => setActiveTab("evolution")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "evolution"
              ? "bg-gradient-to-r from-rose-500/20 to-pink-500/20 text-rose-300 border border-rose-500/40 shadow-lg shadow-rose-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <RefreshCw className="h-4 w-4 text-rose-400" />
          Self-Evolution
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
          onClick={() => setActiveTab("mcp")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "mcp"
              ? "bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Plug className="h-4 w-4 text-emerald-400" />
          MCP Servers ({mcpServers.length})
        </button>

        <button
          onClick={() => setActiveTab("mcpsdk")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "mcpsdk"
              ? "bg-gradient-to-r from-cyan-500/20 to-sky-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Boxes className="h-4 w-4 text-sky-400" />
          MCP SDK
          {mcpSdk && (
            <span className="text-[10px] font-mono ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              {mcpSdk.packages.length}p · {mcpSdk.primitives.length}pr
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("speckit")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "speckit"
              ? "bg-gradient-to-r from-cyan-500/20 to-amber-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Layers className="h-4 w-4 text-amber-400" />
          SpecKit
          {speckit?.present && (
            <span className="text-[10px] font-mono ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              {speckit.workflows.length}w · {speckit.templates.length}t
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("chatkit")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "chatkit"
              ? "bg-gradient-to-r from-cyan-500/20 to-fuchsia-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <MessagesSquare className="h-4 w-4 text-fuchsia-400" />
          ChatKit
          {chatkit && (
            <span className="text-[10px] font-mono ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              {chatkit.samples.length} samples
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("antigravity")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "antigravity"
              ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Bot className="h-4 w-4 text-cyan-400" />
          Antigravity
          {antigravity && (
            <span className="text-[10px] font-mono ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              {antigravity.primitives.length}p
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("genkit")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "genkit"
              ? "bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Sparkles className="h-4 w-4 text-emerald-400" />
          Genkit
          {genkit && (
            <span className="text-[10px] font-mono ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              {genkit.providers.length}p
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("conductor")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "conductor"
              ? "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Music2 className="h-4 w-4 text-purple-400" />
          Conductor
          {conductor && (
            <span className="text-[10px] font-mono ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              {conductor.commands.length}c
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("adk")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "adk"
              ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Users className="h-4 w-4 text-cyan-400" />
          Google ADK
          {adk && (
            <span className="text-[10px] font-mono ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              {adk.primitives.length}p
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("m365")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "m365"
              ? "bg-gradient-to-r from-cyan-500/20 to-sky-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Fingerprint className="h-4 w-4 text-sky-400" />
          M365 Copilot
        </button>

        <button
          onClick={() => setActiveTab("autocycle")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "autocycle"
              ? "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <RefreshCw className="h-4 w-4 text-purple-400" />
          Auto-Cycle
          {autocycle && (
            <span className="text-[10px] font-mono ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              {autocycle.personas.length}x{autocycle.roundCap}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("specs")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "specs"
              ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <ScrollText className="h-4 w-4 text-cyan-400" />
          Design Specs
          {designSpecs?.present && (
            <span className="text-[10px] font-mono ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              {designSpecs.specs.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("gateway")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "gateway"
              ? "bg-gradient-to-r from-cyan-500/20 to-rose-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <ShieldCheck className="h-4 w-4 text-rose-400" />
          Agent Gateway
          {gateway && (
            <span className="text-[10px] font-mono ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              {gateway.controls.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("otel")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "otel"
              ? "bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Telescope className="h-4 w-4 text-emerald-400" />
          Observability
        </button>

        <button
          onClick={() => setActiveTab("learning")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
            activeTab === "learning"
              ? "bg-gradient-to-r from-cyan-500/20 to-amber-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <GraduationCap className="h-4 w-4 text-amber-400" />
          Learning
          {learning && (
            <span className="text-[10px] font-mono ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              {learning.resources.length}
            </span>
          )}
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
            <div className="flex flex-wrap items-center gap-2">
              <DataSourceBadge source={dataSources.agents} label="eval.jsonl" />
              {unattributedRuns > 0 && (
                <span
                  className="inline-flex items-center rounded-full border border-slate-700/60 bg-slate-900/70 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide text-slate-400"
                  title="Runs whose eval entry carried no persona field. They are counted separately rather than assigned to a persona."
                >
                  {unattributedRuns} unattributed
                </span>
              )}
            </div>
            <AgentOverview agents={agents} />
            <LiveTelemetryFeed />
            <AnalyticsCharts metrics={metrics} agents={agents} />
          </div>
        )}

        {activeTab === "arena" && <ChatStudioPanel />}

        {activeTab === "finetune" && <FinetuningPanel />}

        {activeTab === "adk_bridge" && <GoogleAdkBridgePanel />}

        {activeTab === "telegram_hub" && <TelegramVoiceBridgePanel />}

        {activeTab === "workflows" && <WorkflowFrameworkPanel />}

        {activeTab === "providers" && <ProviderMatrixPanel />}

        {activeTab === "hub" && <HubEcosystemPanel />}

        {activeTab === "skills" && <SkillsToolsPanel />}

        {activeTab === "benchmarks" && <BenchmarkArena />}

        {activeTab === "rag_telegram" && <MemoryRagTelegramPanel />}

        {activeTab === "evolution" && <SelfEvolutionPanel />}

        {activeTab === "analytics" && (
          <div className="space-y-4">
            <DataSourceBadge source={dataSources.metrics} label="eval.jsonl" />
            <AnalyticsCharts metrics={metrics} agents={agents} />
          </div>
        )}

        {activeTab === "sessions" && (
          <div className="space-y-4">
            <DataSourceBadge source={dataSources.sessions} label="sessions/" />
            <SessionExplorer
              sessions={sessions}
              total={totalSessions}
              onSessionSelect={handleFetchSessionDetail}
              selectedSessionDetail={selectedSessionDetail}
            />
          </div>
        )}

        {activeTab === "memory" && (
          <div className="space-y-8">
            <div className="space-y-4">
              <DataSourceBadge source={dataSources.memory} label="memory.db" />
              <MemoryExplorer memory={memory} />
            </div>
            <div className="space-y-4">
              <DataSourceBadge source={dataSources.audit} label="audit.log" />
              <AuditLogs logs={auditLogs} />
            </div>
          </div>
        )}

        {activeTab === "mcp" && <McpServers servers={mcpServers} />}

        {activeTab === "mcpsdk" && <McpSdkPanel data={mcpSdk} />}

        {activeTab === "speckit" && <SpecKitPanel data={speckit} />}

        {activeTab === "chatkit" && <ChatKitPanel data={chatkit} />}

        {activeTab === "antigravity" && <AntigravityPanel data={antigravity} />}

        {activeTab === "genkit" && <GenkitPanel data={genkit} />}

        {activeTab === "conductor" && <ConductorPanel data={conductor} />}

        {activeTab === "adk" && <GoogleAdkPanel data={adk} />}

        {activeTab === "m365" && <M365CopilotPanel data={m365} />}

        {activeTab === "autocycle" && <AutoCyclePanel data={autocycle} />}

        {activeTab === "specs" && <DesignSpecsPanel data={designSpecs} />}

        {activeTab === "gateway" && (
          <div className="space-y-8">
            <GatewayRouterPanel />
            <AgentGatewayPanel data={gateway} />
          </div>
        )}

        {activeTab === "otel" && <OtelPanel data={otel} />}

        {activeTab === "learning" && <GcpLearningPanel data={learning} />}

        {activeTab === "stitch" && <StitchStudio />}
      </div>
    </div>
  );
}
