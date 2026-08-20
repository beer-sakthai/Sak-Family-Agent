"use client";

import { useState, useEffect, useCallback, useRef } from "react";
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

/**
 * The full set of telemetry the dashboard renders, bundled into one object so
 * panels and the tab registry receive a single `data` argument instead of ~20
 * individually-threaded props (Introduce Parameter Object).
 */
export interface DashboardData {
  agents: AgentPersona[];
  metrics: MetricsData;
  memory: MemoryData;
  auditLogs: AuditLog[];
  sessions: SessionMeta[];
  totalSessions: number;
  dataSources: {
    agents?: DataSource;
    metrics?: DataSource;
    memory?: DataSource;
    audit?: DataSource;
    sessions?: DataSource;
  };
  unattributedRuns: number;
  mcpServers: McpServerSpec[];
  speckit: SpecKitData | null;
  mcpSdk: McpSdkData | null;
  chatkit: ChatKitData | null;
  antigravity: AntigravityData | null;
  genkit: GenkitData | null;
  conductor: ConductorData | null;
  otel: OtelData | null;
  adk: AdkData | null;
  learning: GcpLearningData | null;
  m365: M365CopilotData | null;
  gateway: GatewayData | null;
  autocycle: AutoCycleData | null;
  designSpecs: DesignSpecsData | null;
}

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

/**
 * Central data-fetching hook (Custom Hook pattern).
 *
 * `page.tsx` used to own ~30 `useState` calls, an 18-fetch `Promise.all`, and
 * the demo-toggle refetch effect inline. That lifecycle is the same for every
 * consumer of the dashboard, so it lives here once. The hook returns a single
 * `data` bundle plus the controls the page needs (`isDemo`, `toggleDemo`,
 * `refresh`, and the session-detail fetch).
 */
export function useDashboardData() {
  const [isDemo, setIsDemo] = useState(false);
  const [agents, setAgents] = useState<AgentPersona[]>(defaultPersonas);
  const [metrics, setMetrics] = useState<MetricsData>(defaultMetrics);
  const [memory, setMemory] = useState<MemoryData>(defaultMemory);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>(defaultAuditLogs);
  const [sessions, setSessions] = useState<SessionMeta[]>(defaultSessions);
  const [totalSessions, setTotalSessions] = useState<number>(DEMO_TOTAL_RUNS);
  // Per-panel provenance, so the UI can say whether what is on screen was
  // measured. Without it a machine with no ~/.sakthai renders a fully populated
  // dashboard indistinguishable from a busy one.
  const [dataSources, setDataSources] = useState<DashboardData["dataSources"]>({});
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

  const isMountedRef = useRef(true);

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

  const toggleDemo = useCallback((newVal?: boolean) => {
    const nextVal = typeof newVal === "boolean" ? newVal : !isDemo;
    setIsDemo(nextVal);
  }, [isDemo]);

  const fetchSessionDetail = useCallback(async (sessionId: string) => {
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
  }, [isDemo]);

  const data: DashboardData = {
    agents,
    metrics,
    memory,
    auditLogs,
    sessions,
    totalSessions,
    dataSources,
    unattributedRuns,
    mcpServers,
    speckit,
    mcpSdk,
    chatkit,
    antigravity,
    genkit,
    conductor,
    otel,
    adk,
    learning,
    m365,
    gateway,
    autocycle,
    designSpecs,
  };

  return {
    data,
    isLoading,
    isDemo,
    toggleDemo,
    refresh: () => fetchAllData(isDemo),
    selectedSessionDetail,
    fetchSessionDetail,
  };
}
