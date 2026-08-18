/**
 * Where a panel's numbers came from.
 *
 * `live`        — read from a real file under SAKTHAI_DIR.
 * `demo`        — synthesized sample data (demo toggle, or a source that failed to parse).
 * `unavailable` — the source file does not exist. Distinct from `demo` on purpose:
 *                 the app ships with demo data so it renders on a fresh checkout,
 *                 and without this distinction a machine with no ~/.sakthai looks
 *                 identical to a busy one.
 */
export type DataSource = "live" | "demo" | "unavailable";

export interface AgentPersona {
  /** Slug matching config.PERSONA_NAMES; absent on the unattributed bucket. */
  slug?: string;
  name: string;
  role: string;
  status: string;
  model: string;
  provider?: string;
  latencyMs: number;
  runs: number;
  skills: string[];
  badge?: string;
  benchmarkScore?: number;
  /** True for the synthetic "Unattributed" row, which is not a real persona. */
  unattributed?: boolean;
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

export interface MemoryCacheMetrics {
  hitRate: number;
  l1Hits: number;
  misses: number;
  totalRequests: number;
  cachedShardsCount: number;
  latencyAvgMs: number;
}

export interface MemoryData {
  facts: FactRecord[];
  observations: ObservationRecord[];
  /** Per-shard read outcome, so the UI can show which personas' memory was reachable. */
  shards?: MemoryShardStatus[];
  cacheMetrics?: MemoryCacheMetrics;
}

/**
 * One memory database the dashboard tried to read.
 *
 * Deployed personas run with `SAKTHAI_HOME=$HOME/.sakthai/$AGENT`
 * (`infra/vm-agents/sakthai-agent-run.sh`), so each writes to its own shard at
 * `~/.sakthai/<persona>/memory.db` rather than the legacy unscoped `memory.db`.
 * Mirrors `config.persona_memory_db_path()` and `FamilyMemoryView`.
 */
export interface MemoryShardStatus {
  /** Persona slug, or "legacy" for the unscoped ~/.sakthai/memory.db. */
  persona: string;
  path: string;
  exists: boolean;
  factCount: number;
  observationCount: number;
  /** Set when the shard exists but could not be opened or queried. */
  error?: string;
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
  dataSource?: DataSource;
  /** Runs that carried no usable persona attribution, so callers can show the gap. */
  unattributedRuns?: number;
  error?: string;
}

export interface MetricsApiResponse {
  success: boolean;
  metrics: MetricsData;
  dataSource?: DataSource;
  error?: string;
}

export interface MemoryApiResponse {
  success: boolean;
  memory: MemoryData;
  auditLogs: AuditLog[];
  dataSource?: DataSource;
  auditDataSource?: DataSource;
  error?: string;
}

export interface SessionsApiResponse {
  success: boolean;
  sessions: SessionMeta[];
  total: number;
  detail?: SessionTranscript;
  dataSource?: DataSource;
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
  upstream: SpecKitUpstream;
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

// ---------------- OpenTelemetry (Observability) ----------------

export type OtelSignal = "traces" | "metrics" | "logs";

export interface OtelSignalCard {
  id: OtelSignal;
  title: string;
  summary: string;
  keyPrimitives: string[];
  docsUrl: string;
}

export interface OtelExporter {
  id: string;
  name: string;
  transport: string;
  usage: string;
}

export interface OtelSemConv {
  attribute: string;
  purpose: string;
}

export interface OtelData {
  overview: {
    title: string;
    description: string;
    repoUrl: string;
    siteUrl: string;
    license: string;
  };
  install: string;
  signals: OtelSignalCard[];
  exporters: OtelExporter[];
  llmSemconv: OtelSemConv[];
  sakthaiIntegration: string;
}

export interface OtelApiResponse {
  success: boolean;
  otel: OtelData;
  error?: string;
}

// ---------------- Google ADK ----------------

export type AdkPrimitiveKind =
  | "core"
  | "llm-agent"
  | "workflow-agent"
  | "runner"
  | "tool"
  | "mcp"
  | "cli";

export interface AdkPrimitive {
  id: string;
  name: string;
  kind: AdkPrimitiveKind;
  summary: string;
  snippet: string;
}

export interface AdkAppField {
  field: string;
  type: string;
  defaultValue: string;
  description: string;
}

export interface AdkPlugin {
  name: string;
  importPath: string;
  purpose: string;
}

export interface AdkCrossCuttingConfig {
  id: string;
  name: string;
  importPath: string;
  purpose: string;
  experimental: boolean;
}

export interface AdkA2aService {
  name: string;
  role: string;
  kind: "orchestrator" | "worker" | "app";
}

export interface AdkData {
  overview: {
    title: string;
    description: string;
    repoUrl: string;
    docsUrl: string;
    pypiUrl: string;
    packageName: string;
    license: string;
    pythonMin: string;
  };
  install: string;
  quickstart: string;
  primitives: AdkPrimitive[];
  cliCommands: Array<{ command: string; purpose: string }>;
  comparisonNote: string;
  app: {
    intro: string;
    snippet: string;
    runnerSnippet: string;
    fields: AdkAppField[];
    plugins: AdkPlugin[];
    configs: AdkCrossCuttingConfig[];
    configSnippet: string;
    legacyNote: string;
    legacySnippet: string;
    legacyDifferences: string[];
    nameRules: string;
    limitations: string[];
  };
  a2a: {
    intro: string;
    services: AdkA2aService[];
    agentCardPath: string;
    snippet: string;
    envVars: Array<{ key: string; value: string }>;
    sharedFiles: Array<{ file: string; purpose: string }>;
  };
}

export interface AdkApiResponse {
  success: boolean;
  adk: AdkData;
  error?: string;
}

// ---------------- Agent Gateway (governance) ----------------

export interface GatewayControl {
  id: string;
  name: string;
  kind: "authz" | "content" | "discovery" | "identity" | "observability";
  summary: string;
  enforcedAt: string;
}

export interface GatewayMode {
  mode: string;
  cloudRunIngress: string;
  registryUrls: string;
  extraRequirements: string;
  secure: boolean;
}

export interface GatewayMcpService {
  name: string;
  purpose: string;
}

export interface GatewayStep {
  order: number;
  title: string;
  command: string;
}

export interface GatewayData {
  overview: {
    title: string;
    description: string;
    repoUrl: string;
    codelabUrl: string;
    license: string;
  };
  controls: GatewayControl[];
  modes: GatewayMode[];
  mcpServices: GatewayMcpService[];
  prerequisites: string[];
  steps: GatewayStep[];
  sakthaiRelevance: string;
}

export interface GatewayApiResponse {
  success: boolean;
  gateway: GatewayData;
  error?: string;
}

// ---------------- Sak Family Auto-Cycle ----------------

export interface CycleStage {
  stage: string;
  number: number;
  goal: string;
  commands: string[];
  guidance: string;
}

export interface CyclePersonaDispatch {
  persona: string;
  liveHome: string;
  lead?: boolean;
}

export interface AutoCycleSkill {
  name: string;
  path: string;
  layer: "shared" | "claude-code";
  purpose: string;
}

export interface AutoCycleData {
  overview: {
    title: string;
    description: string;
    specPath: string;
    planPath: string;
    skillPath: string;
  };
  stages: CycleStage[];
  personas: CyclePersonaDispatch[];
  skills: AutoCycleSkill[];
  roundCap: number;
  safetyRule: {
    headline: string;
    body: string;
    testCommand: string;
    liveAuthorizationPhrases: string[];
    nonAuthorizationPhrases: string[];
    baselineEvidence: string;
  };
  dispatchNote: string;
  errorHandling: string;
  resolvedGap: string;
  cliCommands: Array<{ command: string; purpose: string }>;
}

export interface AutoCycleApiResponse {
  success: boolean;
  autocycle: AutoCycleData;
  error?: string;
}

// ---------------- Design specs index ----------------

export type SpecStatus = "approved" | "draft" | "implemented" | "unknown";

export interface DesignSpec {
  id: string;
  file: string;
  title: string;
  date: string;
  status: SpecStatus;
  statusRaw: string;
  summary: string;
  planFile?: string;
  relatedTab?: string;
  bytes: number;
}

export interface DesignSpecsData {
  present: boolean;
  specsDir: string;
  plansDir: string;
  specs: DesignSpec[];
}

export interface DesignSpecsApiResponse {
  success: boolean;
  specs: DesignSpecsData;
  error?: string;
}

// ---------------- GCP Learning (training-data-analyst) ----------------

export type GcpLearningTag =
  | "agents"
  | "ml"
  | "data"
  | "notebooks"
  | "labs"
  | "docs";

export interface GcpLearningResource {
  id: string;
  path: string;
  title: string;
  description: string;
  tags: GcpLearningTag[];
  url: string;
}

export interface GcpLearningData {
  overview: {
    title: string;
    description: string;
    repoUrl: string;
    stars: string;
    license: string;
  };
  resources: GcpLearningResource[];
  tagLabels: Record<GcpLearningTag, string>;
}

export interface GcpLearningApiResponse {
  success: boolean;
  learning: GcpLearningData;
  error?: string;
}

// ---------------- SpecKit upstream (enhancement) ----------------

export interface SpecKitUpstreamCommand {
  slash: string;
  purpose: string;
  optional?: boolean;
}

export interface SpecKitUpstream {
  repoUrl: string;
  license: string;
  installCommand: string;
  minPython: string;
  requiredTools: string[];
  supportedIntegrations: string[];
  commands: SpecKitUpstreamCommand[];
  layoutNote: string;
}

// ---------------- M365 Copilot Agents ----------------

export interface M365CopilotPrimitive {
  id: string;
  name: string;
  summary: string;
  snippet: string;
}

export interface M365CopilotData {
  overview: {
    title: string;
    description: string;
    repoUrl: string;
    pypiUrl: string;
    packageName: string;
    authModel: string;
  };
  install: string;
  quickstart: string;
  primitives: M365CopilotPrimitive[];
  authSteps: string[];
  contrastWithTeamsMcp: Array<{
    dimension: string;
    m365Sdk: string;
    teamsCopilotMcp: string;
  }>;
}

export interface M365CopilotApiResponse {
  success: boolean;
  m365: M365CopilotData;
  error?: string;
}

// ---------------- Real-Time Telemetry & SSE Streaming ----------------

export type TelemetryEventType =
  | "connected"
  | "agent_start"
  | "agent_message"
  | "agent_dispatch"
  | "agent_step"
  | "token_delta"
  | "tool_call"
  | "tool_result"
  | "guardrail_check"
  | "memory_mutation"
  | "agent_complete"
  | "agent_error"
  | "heartbeat";

export interface TelemetryEvent {
  id: string;
  type: TelemetryEventType;
  timestamp: string;
  persona: string;
  sessionId?: string;
  data: {
    message?: string;
    tokensGenerated?: number;
    latencyMs?: number;
    toolName?: string;
    toolArgs?: Record<string, unknown>;
    toolOutput?: unknown;
    guardrailAction?: "ALLOW" | "DENY" | "MODIFY";
    guardrailRule?: string;
    memoryKey?: string;
    memoryVal?: string;
    error?: string;
    task?: string;
    step?: string;
    phase?: string;
    status?: string;
    dispatchedAt?: string;
    parameters?: Record<string, unknown>;
  };
}

export interface StreamEventPayload {
  event: TelemetryEventType;
  payload: TelemetryEvent;
}

// ---------------- Multi-Provider Ecosystem & Workflow Framework ----------------

export type ProviderType =
  | "claude"
  | "codex"
  | "opencode"
  | "ollama"
  | "huggingface"
  | "gemini_agy"
  | "m365_azure";

export interface ModelSpec {
  id: string;
  name: string;
  contextWindow: number;
  inputCostPer1M: number;
  outputCostPer1M: number;
  isLocal: boolean;
  capabilities: ("text" | "vision" | "code" | "tool_calling" | "reasoning")[];
}

export interface ProviderSpec {
  id: ProviderType;
  name: string;
  description: string;
  vendor: string;
  badge: string;
  health: "healthy" | "degraded" | "offline";
  latencyMs: number;
  supportedModels: ModelSpec[];
  defaultModel: string;
  isLocal: boolean;
  assignedPersonas: string[];
}

export interface WorkflowStage {
  id: string;
  name: string;
  personaSlug: string;
  personaName: string;
  provider: ProviderType;
  model: string;
  action: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  durationMs?: number;
  tokensUsed?: number;
  outputSummary?: string;
  dependsOn?: string[];
  params?: Record<string, any>;
  output?: Record<string, any>;
  condition?: string;
  retryCount?: number;
}

export interface WorkflowTopology {
  id: string;
  name: string;
  description: string;
  category: "autonomous" | "security" | "publishing" | "maintenance";
  stages: WorkflowStage[];
}

export interface WorkflowExecutionResult {
  executionId: string;
  workflowId: string;
  status: "running" | "completed" | "failed";
  startTime: string;
  endTime?: string;
  stages: WorkflowStage[];
  totalTokens: number;
  totalLatencyMs: number;
}

// ---------------- 6-Part Cycle Intelligence & Operations Suite ----------------

// Part 1: Dream · Hub Ecosystem
export interface ModelCardMeta {
  pipelineTag?: string;
  license: string;
  downloads: number;
  likes: number;
  tags: string[];
  hasGGUF: boolean;
  quantizations: string[];
}

export interface HubAsset {
  id: string;
  name: string;
  type: "model" | "dataset" | "space";
  repoId: string;
  author: string;
  url: string;
  meta: ModelCardMeta;
  status: "active" | "building" | "archived";
}

export interface HubEcosystemData {
  totalModels: number;
  totalDatasets: number;
  totalSpaces: number;
  assets: HubAsset[];
  syncedAt: string;
}

// Part 2: Hope · Skills & Tool Calling
export interface ToolGuardrailSpec {
  name: string;
  category: "shell" | "filesystem" | "network" | "credentials" | "ast";
  level: "allow" | "prompt" | "deny";
  ruleDescription: string;
  blockedPatterns?: string[];
}

export interface SkillSpec {
  slug: string;
  name: string;
  description: string;
  category: "system" | "automation" | "research" | "creative" | "testing";
  authorPersona: string;
  commandSnippet: string;
  requiredTools: string[];
  guardrailCount: number;
}

export interface ASTAuditResult {
  allowedCount: number;
  blockedCount: number;
  activeRules: ToolGuardrailSpec[];
}

export interface SkillsCatalogData {
  skills: SkillSpec[];
  guardrails: ToolGuardrailSpec[];
  totalSkills: number;
  totalTools: number;
}

// Part 4: Joy · Benchmark Arena
export type BenchmarkCategory = "MMLU" | "HumanEval" | "GSM8k" | "ToolAccuracy" | "SafetyRefusal";

export interface BenchmarkEvalItem {
  id: string;
  category: BenchmarkCategory;
  name: string;
  description: string;
  sampleCount: number;
  averageLatencyMs: number;
}

export interface PersonaBenchmarkScore {
  personaSlug: string;
  personaName: string;
  model: string;
  provider: ProviderType;
  overallScore: number;
  categoryScores: Record<BenchmarkCategory, number>;
  tokensPerSec: number;
  costPer1kRuns: number;
}

export interface BenchmarkArenaData {
  leaderboard: PersonaBenchmarkScore[];
  evalCategories: BenchmarkEvalItem[];
  testedAt: string;
}

// Part 5: Trust · Memory Vector RAG & Telegram
export interface KnowledgeNode {
  id: string;
  label: string;
  type: "persona" | "fact" | "task" | "session" | "rule";
  val: number;
  color?: string;
}

export interface KnowledgeEdge {
  source: string;
  target: string;
  relation: string;
}

export interface KnowledgeGraphData {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
  totalFacts: number;
  dbPath: string;
}

export interface TelegramBridgeData {
  botUsername: string;
  status: "online" | "polling" | "idle";
  activeSessions: number;
  registeredCommands: string[];
  voiceTranscriberEnabled: boolean;
  allowedUserCount: number;
}

// Part 6: Growth · Self-Evolution Loop
export interface PromptEvolutionItem {
  id: string;
  personaSlug: string;
  timestamp: string;
  originalSnippet: string;
  evolvedSnippet: string;
  rationale: string;
  performanceDelta: string;
}

export interface LearningJournalEntry {
  id: string;
  timestamp: string;
  persona: string;
  triggerEvent: string;
  lessonLearned: string;
  remediationApplied: boolean;
}

export interface SelfEvolutionData {
  round: number;
  evolutions: PromptEvolutionItem[];
  journalEntries: LearningJournalEntry[];
  mutationCoveragePct: number;
  lastWrapTimestamp: string;
}

// -------------------------------------------------------------
// Sak-Agent Collaborative Chat Arena & Studio Types
// -------------------------------------------------------------

export type PersonaPresetId = 'cloud_powerhouse' | 'local_offline' | 'fast_efficient' | 'custom';

export interface PersonaPreset {
  id: PersonaPresetId;
  name: string;
  description: string;
  icon: string;
  personaMappings: Record<string, { provider: string; model: string }>;
}

export interface SupervisorSubTask {
  id: string;
  persona: string;
  goal: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  assignedAt: number;
  resultSummary?: string;
}

export interface SupervisorPlan {
  sessionId: string;
  taskGoal: string;
  supervisor: string;
  subtasks: SupervisorSubTask[];
  consensusApproach: string;
  createdAt: number;
}

export interface ToolApprovalRequest {
  callId: string;
  persona: string;
  tool: string;
  args: Record<string, unknown>;
  reason: string;
  destructive: boolean;
  astScore: number;
  status: 'pending' | 'approved' | 'rejected';
}

export interface ASTValidationResult {
  isSafe: boolean;
  score: number; // 0 - 100
  violations: string[];
  requiresApproval: boolean;
  severity: 'safe' | 'warning' | 'dangerous';
}

export interface DatasetStagingEntry {
  id: string;
  timestamp: string;
  sessionId: string;
  instruction: string;
  personasInvolved: string[];
  reasoningTraces: Array<{ persona: string; thought: string; toolsUsed: string[] }>;
  finalOutput: string;
  stagedBy: 'auto_heuristic' | 'user_star';
  heuristicScore: number;
  scrubbedPII: boolean;
}

export type SSEChatEvent =
  | { type: 'session_start'; sessionId: string; personas: string[]; preset: PersonaPresetId; timestamp: number }
  | { type: 'supervisor_plan'; plan: SupervisorPlan }
  | { type: 'persona_thought'; persona: string; chunk: string; taskId?: string }
  | { type: 'tool_call'; persona: string; tool: string; args: Record<string, unknown>; callId: string }
  | { type: 'tool_approval_required'; approval: ToolApprovalRequest }
  | { type: 'tool_output'; callId: string; output: string; exitCode: number; astSafe: boolean }
  | { type: 'synthesis_chunk'; chunk: string }
  | { type: 'staged_dataset_entry'; entry: DatasetStagingEntry }
  | { type: 'session_complete'; totalTokens: number; durationMs: number };

// -------------------------------------------------------------
// Sak-Agent LoRA Fine-Tuning & Dataset Curation Types
// -------------------------------------------------------------

export type LoraTargetModel = 'sakthai-1.5b' | 'sakthai-7b' | 'qwen-2.5-coder-7b';

export interface LoraTrainingConfig {
  jobId: string;
  modelName: LoraTargetModel;
  datasetPath: string;
  r: number;
  loraAlpha: number;
  loraDropout: number;
  learningRate: number;
  numEpochs: number;
  batchSize: number;
  targetModules: string[];
  outputDir: string;
}

export interface TrainingLossPoint {
  epoch: number;
  step: number;
  loss: number;
  evalLoss?: number;
}

export interface LoraJobStatus {
  jobId: string;
  modelName: LoraTargetModel;
  status: 'pending' | 'running' | 'completed' | 'failed';
  currentEpoch: number;
  totalEpochs: number;
  currentStep: number;
  totalSteps: number;
  lossHistory: TrainingLossPoint[];
  currentLoss: number;
  checkpointPath?: string;
  startedAt: number;
  completedAt?: number;
  errorMessage?: string;
}

export interface DatasetCardSpec {
  id: string;
  name: string;
  format: 'chatml' | 'alpaca' | 'sharegpt';
  totalSamples: number;
  avgTokenLength: number;
  personasCovered: string[];
  hfRepoId: string;
  samples: Array<{ instruction: string; response: string; persona: string }>;
}

// -------------------------------------------------------------
// Google ADK & Cloud Run / GKE Deployment Bridge Types
// -------------------------------------------------------------

export type AdkPrimitiveType = 'LlmAgent' | 'SequentialAgent' | 'ParallelAgent' | 'Tool' | 'Runner';

export interface AdkAgentSpec {
  personaSlug: string;
  name: string;
  role: string;
  primitive: AdkPrimitiveType;
  model: string;
  description: string;
  tools: string[];
  generatedPythonCode: string;
}

export type DeploymentTarget = 'cloud_run' | 'gke';

export interface CloudDeploymentManifest {
  target: DeploymentTarget;
  serviceName: string;
  region: string;
  cpu: string;
  memory: string;
  minInstances: number;
  maxInstances: number;
  serviceAccount: string;
  dockerfile: string;
  manifestYaml: string;
}

export interface QualityFlywheelEvalMetric {
  category: string;
  score: number;
  benchmarkTarget: number;
  status: 'pass' | 'warning' | 'fail';
}

export interface QualityFlywheelEvalResult {
  evalId: string;
  timestamp: string;
  datasetSize: number;
  overallAccuracy: number;
  toolCallingPrecision: number;
  avgLatencyMs: number;
  safetyCompliance: number;
  metrics: QualityFlywheelEvalMetric[];
}

export interface AgentRegistryStatus {
  fleetCount: number;
  publishedToEnterprise: boolean;
  activeInstances: number;
  registryEndpoint: string;
  lastSync: string;
}

// -------------------------------------------------------------
// Telegram Voice Bridge & Mobile Incident Alerting Hub Types
// -------------------------------------------------------------

export type IncidentSeverity = 'P0_CRITICAL' | 'P1_HIGH' | 'P2_MEDIUM' | 'P3_LOW';

export interface MobileIncidentAlert {
  alertId: string;
  severity: IncidentSeverity;
  source: string;
  title: string;
  details: string;
  suggestedAction: string;
  status: 'active' | 'acknowledged' | 'resolved';
  requiresApproval: boolean;
  createdAt: string;
}

export interface PersonaVoiceProfile {
  personaSlug: string;
  name: string;
  voiceId: string;
  pitch: number;
  speed: number;
  toneDescription: string;
  samplePhrase: string;
}

export interface TelegramVoiceMessage {
  messageId: number;
  chatId: number;
  username: string;
  durationSeconds: number;
  transcription: string;
  targetPersona: string;
  responseAudioUrl?: string;
  responseText?: string;
  timestamp: number;
}

export interface TelegramWebhookStatus {
  connected: boolean;
  botUsername: string;
  webhookUrl: string;
  pendingUpdates: number;
  lastUpdateTimestamp: string;
}


