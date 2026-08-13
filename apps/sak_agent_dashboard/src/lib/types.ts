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

export type McpActionStability = "stable" | "beta" | "verify";
export type McpActionCategory =
  | "teams"
  | "chats"
  | "meetings"
  | "calendar"
  | "users"
  | "copilot"
  | "other";

export interface McpAction {
  id: string;
  method: string;
  pathTemplate: string;
  description: string;
  params: string[];
  stability: McpActionStability;
  requiresDelegatedAuth: boolean;
  category: McpActionCategory;
}

export interface McpToolShortcut {
  name: string;
  signature: string;
  description: string;
  disabled?: boolean;
  disabledReason?: string;
}

export interface McpEnvVar {
  key: string;
  purpose: string;
  required: boolean;
}

export interface McpRegistrationTarget {
  label: string;
  path: string;
  format: string;
  snippet: string;
}

export type McpServerStatus = "healthy" | "degraded" | "unconfigured" | "unknown";

export interface McpServerSpec {
  id: string;
  name: string;
  displayName: string;
  description: string;
  category: string;
  transport: "stdio" | "http" | "sse";
  language: string;
  repoPath: string;
  command: string;
  args: string[];
  entrypoint: string;
  status: McpServerStatus;
  statusReason: string;
  envVars: McpEnvVar[];
  tools: McpToolShortcut[];
  actions: McpAction[];
  registrationTargets: McpRegistrationTarget[];
  docsUrl?: string;
  knownLimitations: string[];
}

export interface McpServersApiResponse {
  success: boolean;
  servers: McpServerSpec[];
  error?: string;
}

export interface SpecKitInitOptions {
  ai: string;
  featureNumbering: string;
  here: boolean;
  integration: string;
  script: string;
  speckitVersion: string;
}

export interface SpecKitIntegrationState {
  version: string;
  integrationStateSchema: number;
  installedIntegrations: string[];
  defaultIntegration: string;
  currentIntegration: string;
  integrationSettings: Record<string, Record<string, string>>;
}

export interface SpecKitTemplate {
  name: string;
  path: string;
  bytes: number;
  lines: number;
  preview: string;
}

export type SpecKitWorkflowStepKind = "command" | "gate" | "other";

export interface SpecKitWorkflowStep {
  id: string;
  kind: SpecKitWorkflowStepKind;
  command?: string;
  message?: string;
  options?: string[];
  onReject?: string;
  integration?: string;
}

export interface SpecKitWorkflow {
  id: string;
  name: string;
  version: string;
  description: string;
  installedAt?: string;
  updatedAt?: string;
  author?: string;
  requiresSpeckitVersion?: string;
  inputs: Array<{ name: string; type: string; required: boolean; default?: string; prompt?: string; enum?: string[] }>;
  steps: SpecKitWorkflowStep[];
  rawYaml: string;
}

export interface SpecKitIntegrationManifest {
  integration: string;
  version: string;
  installedAt: string;
  fileCount: number;
  files: string[];
}

export interface SpecKitConstitution {
  path: string;
  isTemplate: boolean;
  lines: number;
  bytes: number;
  preview: string;
}

export interface SpecKitData {
  present: boolean;
  rootPath: string;
  initOptions?: SpecKitInitOptions;
  integrationState?: SpecKitIntegrationState;
  workflows: SpecKitWorkflow[];
  integrations: SpecKitIntegrationManifest[];
  templates: SpecKitTemplate[];
  constitution?: SpecKitConstitution;
  scripts: string[];
}

export interface SpecKitApiResponse {
  success: boolean;
  speckit: SpecKitData;
  error?: string;
}

