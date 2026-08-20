/**
 * types/integrations.ts — Integration types: MCP, OTEL, ADK, Genkit, Conductor, SpecKit,
 * ChatKit, Antigravity, Gateway, SpecKit, Providers, Workflow, etc.
 *
 * Moved from the monolithic types.ts. Imported via the `@/lib/types` barrel
 * (`types/index.ts`), which re-exports everything here.
 */

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
