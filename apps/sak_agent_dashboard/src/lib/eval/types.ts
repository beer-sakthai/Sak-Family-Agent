/**
 * Types & Domain Models for Sak-Family Agent Evaluation & Quality Flywheel Suite.
 *
 * Covers multi-persona benchmark testing, decomposed G-Eval scoring with Chain-of-Thought,
 * bias mitigation metadata, and continuous Quality Flywheel failure triage.
 */

export type EvalMetricDimension =
  | "goal_completion"
  | "tool_precision"
  | "safety_compliance"
  | "latency_cost";

export type EvalFailureCategory =
  | "TOOL_SCHEMA_MISMATCH"
  | "REASONING_HALLUCINATION"
  | "SAFETY_BREACH"
  | "TIMEOUT"
  | "EXECUTION_ERROR"
  | "UNKNOWN";

export interface EvalValidationRubric {
  completionWeight: number; // e.g. 0.40
  toolWeight: number;       // e.g. 0.30
  safetyWeight: number;     // e.g. 0.20
  efficiencyWeight: number; // e.g. 0.10
}

export interface EvalTestCase {
  id: string;
  personaSlug: string;
  name: string;
  category: "coding" | "security" | "architecture" | "data" | "orchestration" | "adversarial";
  inputPrompt: string;
  systemDirectives?: string;
  expectedTools: string[];
  mockToolResponses?: Record<string, unknown>;
  validationRubric: EvalValidationRubric;
  tags?: string[];
  isGolden?: boolean;
  createdAt?: string;
}

export interface EvalTurnTrace {
  stepNumber: number;
  thought: string;
  toolCall?: {
    name: string;
    args: Record<string, unknown>;
  };
  toolResult?: unknown;
  output?: string;
  latencyMs: number;
}

export interface EvalJudgeReasoning {
  goalAnalysis: string;
  toolAnalysis: string;
  safetyAnalysis: string;
  efficiencyAnalysis: string;
}

export interface EvalJudgeScore {
  goalCompletion: number;       // 0-100
  toolPrecision: number;        // 0-100
  safetyCompliance: number;     // 0 or 100 (binary)
  latencyCost: number;          // 0-100
  compositeScore: number;       // 0-100
  reasoning: EvalJudgeReasoning;
  passed: boolean;
  failureCategory?: EvalFailureCategory;
}

export interface EvalRunConfig {
  testSuiteId?: string;
  personaSlugs: string[];
  judgeModel: string;
  concurrency: number;
  enableCoT: boolean;
  enableOrderShuffling: boolean;
  passThreshold: number;
}

export interface EvalRunResult {
  id: string;
  testCaseId: string;
  testCaseName: string;
  personaSlug: string;
  status: "running" | "completed" | "failed";
  traces: EvalTurnTrace[];
  judgeScore?: EvalJudgeScore;
  executionTimeMs: number;
  tokensUsed: {
    prompt: number;
    completion: number;
    total: number;
  };
  createdAt: string;
}

export interface QualityFlywheelDataset {
  id: string;
  name: string;
  description: string;
  persona: string;
  testCases: EvalTestCase[];
  version: string;
  updatedAt: string;
}

export interface FlywheelFailureEntry {
  id: string;
  runId: string;
  personaSlug: string;
  prompt: string;
  traceSummary: string;
  failureCategory: EvalFailureCategory;
  judgeScore: number;
  triageStatus: "unreviewed" | "added_to_golden" | "dismissed";
  timestamp: string;
}

export interface PersonaBenchmarkSummary {
  personaSlug: string;
  personaName: string;
  totalTests: number;
  passRate: number;
  avgCompositeScore: number;
  avgGoalCompletion: number;
  avgToolPrecision: number;
  avgSafetyCompliance: number;
  avgLatencyMs: number;
}

/** Runtime Type Guard for EvalTestCase */
export function isValidEvalTestCase(data: unknown): data is EvalTestCase {
  if (typeof data !== "object" || data === null) return false;
  const d = data as Record<string, unknown>;
  return (
    typeof d.id === "string" &&
    typeof d.personaSlug === "string" &&
    typeof d.name === "string" &&
    typeof d.inputPrompt === "string" &&
    Array.isArray(d.expectedTools) &&
    typeof d.validationRubric === "object" &&
    d.validationRubric !== null
  );
}

/** Runtime Type Guard for EvalRunConfig */
export function isValidEvalRunConfig(data: unknown): data is EvalRunConfig {
  if (typeof data !== "object" || data === null) return false;
  const d = data as Record<string, unknown>;
  return (
    Array.isArray(d.personaSlugs) &&
    typeof d.judgeModel === "string" &&
    typeof d.concurrency === "number" &&
    typeof d.passThreshold === "number"
  );
}
