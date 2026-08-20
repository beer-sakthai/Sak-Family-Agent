/**
 * types/ui.ts — Dashboard UI types: cycle, learning, social, chat, evolution, benchmarks.
 *
 * Moved from the monolithic types.ts. Imported via the `@/lib/types` barrel
 * (`types/index.ts`), which re-exports everything here.
 */

import type { ProviderType } from "./integrations";

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
