// ---------------------------------------------------------------------------
// DO NOT EDIT. Generated from personas/sakthai/sakthai/web/contracts.py by
// scripts/gen_dashboard_types.py. Run that script to regenerate; CI fails if
// this file is out of sync with the Python contract.
// ---------------------------------------------------------------------------

export type DataSource = "local" | "api" | "demo";

export const UNATTRIBUTED = "unattributed";

export interface TokenStats {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface TrendPoint {
  date: string;
  runs: number;
  errors: number;
  avg_latency_ms: number;
  input_tokens: number;
  output_tokens: number;
}

export interface ModelUsage {
  count: number;
  input_tokens: number;
  output_tokens: number;
  avg_latency_s: number;
}

export interface PersonaSummary {
  name: string;
  display_name: string;
  provider: string;
  model: string;
  has_shard: boolean;
  fact_count: number;
  observation_count: number;
  runs: number;
  errors: number;
  avg_latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  last_run_at: number | null;
}

export interface PersonasPayload {
  personas: PersonaSummary[];
  unattributed_runs: number;
}

export interface MetricsPayload {
  total_runs: number;
  error_rate: number;
  avg_latency_ms: number;
  tokens: TokenStats;
  stop_reasons: Record<string, number>;
  per_model: Record<string, ModelUsage>;
  trends: TrendPoint[];
}

export interface SessionMessage {
  role: string;
  content: string;
}

export interface ToolCallRecord {
  name: string;
  is_error: boolean;
}

export interface SessionSummary {
  id: string;
  timestamp: number;
  persona: string | null;
  task: string;
  model: string;
  iterations: number;
  stop_reason: string;
  tokens: TokenStats;
  message_count: number;
  tool_call_count: number;
  had_error: boolean;
}

export interface SessionDetail {
  summary: SessionSummary;
  messages: SessionMessage[];
  result_text: string;
  tool_calls: ToolCallRecord[];
}

export interface SessionsPayload {
  sessions: SessionSummary[];
  total: number;
  detail: SessionDetail | null;
}

export interface FactRecord {
  id: number;
  persona: string;
  kind: string;
  key: string | null;
  value: string;
  tags: string[];
  created_at: number;
  updated_at: number;
}

export interface ObservationRecord {
  id: number;
  persona: string;
  summary: string;
  weight: number;
  confidence: number;
  created_at: number;
}

export interface GrowthSeries {
  labels: string[];
  values: number[];
}

export interface MemoryPayload {
  facts: FactRecord[];
  observations: ObservationRecord[];
  total_facts: number;
  total_observations: number;
  facts_this_week: number;
  observations_this_week: number;
  fact_growth: GrowthSeries;
  observation_growth: GrowthSeries;
  kind_counts: Record<string, number>;
}

export interface AuditEvent {
  timestamp: number;
  type: string;
  severity: string;
  message: string;
  details: Record<string, unknown>;
}

export interface AuditPayload {
  events: AuditEvent[];
  severity_counts: Record<string, number>;
  total: number;
}

export interface WorkflowStepResult {
  step_id: string;
  status: string;
  attempts: number;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number | null;
}

export interface WorkflowRunSummary {
  run_id: string;
  workflow_name: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number | null;
  step_count: number;
  failed_steps: number;
}

export interface WorkflowRunDetail {
  summary: WorkflowRunSummary;
  steps: WorkflowStepResult[];
}

export interface WorkflowsPayload {
  runs: WorkflowRunSummary[];
}

export interface ApiEnvelope<T = unknown> {
  ok: boolean;
  source: DataSource;
  generated_at: string;
  data: T;
}
