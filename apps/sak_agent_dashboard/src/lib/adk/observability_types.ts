/**
 * Domain types for Google ADK Observability, Cloud Trace OpenTelemetry Spans,
 * Prompt-Response Logging, and BigQuery Agent Analytics.
 */

export type SpanKind =
  | 'invoke_workflow'
  | 'invoke_agent'
  | 'call_llm'
  | 'generate_content'
  | 'execute_tool';

export interface OtelTraceSpan {
  spanId: string;
  parentSpanId?: string;
  name: string;
  kind: SpanKind;
  status: 'OK' | 'ERROR';
  startTimeMs: number;
  durationMs: number;
  attributes: {
    agentSlug?: string;
    model?: string;
    toolName?: string;
    promptTokens?: number;
    completionTokens?: number;
    totalTokens?: number;
    costUsd?: number;
    errorReason?: string;
    [key: string]: unknown;
  };
  children?: OtelTraceSpan[];
}

export type SemconvCaptureLevel =
  | 'NO_CONTENT'
  | 'EVENT_ONLY'
  | 'SPAN_ONLY'
  | 'SPAN_AND_EVENT';

export interface BigQueryAgentAnalyticsEvent {
  eventId: string;
  timestamp: string;
  agentSlug: string;
  sessionToken: string;
  eventType: 'llm_call' | 'tool_use' | 'agent_handoff' | 'guardrail_verdict';
  model: string;
  latencyMs: number;
  totalTokens: number;
  costUsd: number;
  bqDatasetId: string;
  gcsLogUri: string;
  astCompliant: boolean;
}

export interface ObservabilityTierConfig {
  cloudTraceEnabled: boolean;
  gcsPromptLoggingEnabled: boolean;
  bqAnalyticsEnabled: boolean;
  semconvLevel: SemconvCaptureLevel;
  logsBucketName: string;
  bqDatasetId: string;
  telemetryProject: string;
}

export interface TraceWaterfallSummary {
  traceId: string;
  rootWorkflow: string;
  totalSpans: number;
  totalDurationMs: number;
  totalTokens: number;
  totalCostUsd: number;
  spans: OtelTraceSpan[];
}
