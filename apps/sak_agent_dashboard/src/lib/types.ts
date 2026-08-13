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

export type SdkPrimitiveKind =
  | "server"
  | "tool"
  | "resource"
  | "prompt"
  | "transport"
  | "client"
  | "context";

export interface SdkPrimitive {
  id: string;
  name: string;
  kind: SdkPrimitiveKind;
  summary: string;
  snippet: string;
  language: "python";
  docsUrl: string;
}

export interface SdkPackage {
  name: string;
  displayName: string;
  role: string;
  pypi: string;
  repoUrl: string;
  license: string;
  installCommand: string;
  usedInRepoAs: string;
  detectedVersionSpec?: string;
}

export interface SdkUsageSite {
  path: string;
  kind: "pyproject" | "import" | "custom-implementation";
  detail: string;
}

export interface SdkScaffoldFile {
  path: string;
  language: "python" | "toml" | "json" | "markdown";
  content: string;
}

export interface McpSdkData {
  overview: {
    title: string;
    description: string;
    protocolVersion: string;
    docsUrl: string;
  };
  packages: SdkPackage[];
  primitives: SdkPrimitive[];
  usageSites: SdkUsageSite[];
  scaffold: {
    name: string;
    description: string;
    files: SdkScaffoldFile[];
  };
}

export interface McpSdkApiResponse {
  success: boolean;
  sdk: McpSdkData;
  error?: string;
}

export type ChatKitCapability =
  | "server-tools"
  | "client-state"
  | "widgets"
  | "widget-actions"
  | "attachments"
  | "speech-input"
  | "entity-tagging"
  | "dynamic-thread-titles"
  | "image-generation"
  | "route-visualization";

export interface ChatKitSample {
  id: string;
  name: string;
  displayName: string;
  description: string;
  domain: string;
  port: number;
  runCommandFromRoot: string;
  runCommandStandalone: string;
  frontend: string;
  backend: string;
  capabilities: ChatKitCapability[];
  highlights: string[];
}

export interface ChatKitPrerequisite {
  label: string;
  detail: string;
  envVar?: string;
  installCommand?: string;
}

export interface ChatKitData {
  overview: {
    title: string;
    description: string;
    repoUrl: string;
  };
  prerequisites: ChatKitPrerequisite[];
  samples: ChatKitSample[];
  capabilityLabels: Record<ChatKitCapability, string>;
}

export interface ChatKitApiResponse {
  success: boolean;
  chatkit: ChatKitData;
  error?: string;
}

export type AntigravityPrimitiveKind =
  | "agent"
  | "config"
  | "conversation"
  | "response"
  | "loop"
  | "tool"
  | "hook"
  | "mcp";

export interface AntigravityPrimitive {
  id: string;
  name: string;
  kind: AntigravityPrimitiveKind;
  summary: string;
  snippet: string;
  language: "python";
  docsAnchor?: string;
}

export interface AntigravityFeature {
  id: string;
  title: string;
  description: string;
  category: "multimodal" | "tools" | "mcp" | "policy" | "background" | "streaming";
}

export interface AntigravityComparisonRow {
  dimension: string;
  antigravity: string;
  chatkit: string;
  mcpSdk: string;
}

export interface AntigravityData {
  overview: {
    title: string;
    description: string;
    repoUrl: string;
    docsUrl: string;
    license: string;
    author: string;
    pypiUrl: string;
    packageName: string;
  };
  install: {
    pypi: string;
    warning: string;
  };
  quickstart: string;
  primitives: AntigravityPrimitive[];
  features: AntigravityFeature[];
  comparison: AntigravityComparisonRow[];
}

export interface AntigravityApiResponse {
  success: boolean;
  antigravity: AntigravityData;
  error?: string;
}

export type GenkitPrimitiveKind =
  | "core"
  | "decorator"
  | "generation"
  | "session"
  | "model";

export interface GenkitPrimitive {
  id: string;
  name: string;
  kind: GenkitPrimitiveKind;
  summary: string;
  snippet: string;
  language: "python";
}

export interface GenkitProvider {
  id: string;
  name: string;
  packageName: string;
  description: string;
  supported: boolean;
}

export interface GenkitData {
  overview: {
    title: string;
    description: string;
    repoUrl: string;
    pypiUrl: string;
    packageName: string;
    license: string;
    author: string;
    pythonMin: string;
  };
  install: string;
  quickstart: string;
  primitives: GenkitPrimitive[];
  providers: GenkitProvider[];
  distinctiveFeatures: string[];
}

export interface GenkitApiResponse {
  success: boolean;
  genkit: GenkitData;
  error?: string;
}

export interface ConductorHost {
  id: string;
  name: string;
  installCommand: string;
  note: string;
  primary?: boolean;
}

export interface ConductorCommand {
  slash: string;
  purpose: string;
  category: "setup" | "track" | "implement" | "status" | "revert" | "review";
}

export interface ConductorArtifact {
  path: string;
  purpose: string;
  scope: "project" | "track";
}

export interface ConductorData {
  overview: {
    title: string;
    description: string;
    repoUrl: string;
    methodology: string;
  };
  hosts: ConductorHost[];
  commands: ConductorCommand[];
  artifacts: ConductorArtifact[];
  workflow: string[];
  liveDevCommand: string;
}

export interface ConductorApiResponse {
  success: boolean;
  conductor: ConductorData;
  error?: string;
}

