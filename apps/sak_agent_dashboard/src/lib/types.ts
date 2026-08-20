export interface AgentPersona {
  name: string;
  role: string;
  status: string;
  model: string;
  latencyMs: number;
  runs: number;
  skills: string[];
  badge?: string;
  benchmarkScore?: number;
}

export type PersonaCard = AgentPersona;

export interface TokenStats {
  totalTokens: number;
  promptTokens: number;
  completionTokens: number;
}

export interface MetricTrendPoint {
  date: string;
  runs: number;
  latencyMs: number;
}

export interface MetricsData {
  totalRuns: number;
  avgLatencyMs: number;
  successRate: number;
  tokenStats: TokenStats;
  stopReasons: Record<string, number>;
  trends: MetricTrendPoint[];
}

export interface FactRecord {
  id: string | number;
  entity: string;
  fact: string;
  persona?: string;
  createdAt?: string;
}

export interface ObservationRecord {
  id: string | number;
  category: string;
  observation: string;
  timestamp?: string;
}

export interface MemoryData {
  facts: FactRecord[];
  observations: ObservationRecord[];
}

export type AuditSeverity = "info" | "warning" | "error" | "critical";

export interface AuditLog {
  id: string | number;
  timestamp: string;
  persona: string;
  severity: AuditSeverity;
  event: string;
  details: string;
}

export interface SessionMessage {
  role: string;
  content: string;
  timestamp?: string;
  name?: string;
}

export interface SessionMeta {
  sessionId: string;
  persona: string;
  timestamp: string;
  messageCount: number;
  tokenUsage: number;
  status: string;
}

export interface SessionTranscript extends SessionMeta {
  task?: string;
  model?: string;
  messages?: SessionMessage[];
  result?: {
    text?: string;
    iterations?: number;
    stop_reason?: string;
    tool_calls?: any[];
    [key: string]: any;
  };
}

export interface AgentsApiResponse {
  success: boolean;
  agents: AgentPersona[];
  error?: string;
}

export interface MetricsApiResponse {
  success: boolean;
  metrics: MetricsData;
  error?: string;
}

export interface MemoryApiResponse {
  success: boolean;
  memory: MemoryData;
  auditLogs: AuditLog[];
  error?: string;
}

export interface SessionsApiResponse {
  success: boolean;
  sessions: SessionMeta[];
  total: number;
  detail?: SessionTranscript;
  error?: string;
}

export interface StitchScreenPreset {
  id: string;
  title: string;
  category: string;
  prompt: string;
  codeSnippet: string;
  displayMode: "HTML" | "MARKDOWN" | "CODE" | "MERMAID";
  theme: "dark-glassmorphism" | "midnight-emerald" | "cyber-cyan";
}

