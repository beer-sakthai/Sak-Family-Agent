/**
 * The one demo dataset.
 *
 * This previously existed three times — in `lib/sakthai.ts` (`benchmarkScore:
 * 0.96`), in `app/page.tsx` as `defaultPersonas` (`benchmarkScore: 96.5`), and
 * again inline in `src/tests/api.test.ts` — with the same field on two
 * different scales and no normalisation at the render site. One definition,
 * shaped exactly like the contract, so demo and live data render identically.
 *
 * Everything here is deterministic. Nothing calls `Math.random()`: a demo that
 * renders differently on each request cannot be asserted against.
 */

import {
  PERSONA_NAMES,
  type AuditEvent,
  type AuditPayload,
  type FactRecord,
  type GrowthSeries,
  type MemoryPayload,
  type MetricsPayload,
  type ObservationRecord,
  type PersonaSummary,
  type PersonasPayload,
  type SessionSummary,
  type SessionsPayload,
  type TrendPoint,
  type WorkflowRunSummary,
  type WorkflowsPayload,
} from "./contracts.generated";
import { displayName } from "./runtime";

/** A fixed instant, so demo output is byte-stable across requests and tests. */
const EPOCH = 1_787_000_000;
const DAY = 86_400;

const MODELS: Record<string, [string, string]> = {
  sakking: ["huggingface", "Qwen/Qwen3-Coder-30B-A3B-Instruct"],
  sakthai: ["huggingface", "gemini-3.1-flash-lite"],
  saksee: ["huggingface", "gemini-3.1-flash-lite"],
  saksit: ["huggingface", "DeepSeek-V4-Flash"],
  sakjules: ["huggingface", "gemini-2.5-flash-lite"],
  saktan: ["ollama", "sakthai"],
};

/** Per-persona demo run counts. Deliberately uneven, and one persona idle. */
const RUNS: Record<string, number> = {
  sakking: 82,
  sakthai: 214,
  saksee: 137,
  saksit: 46,
  sakjules: 91,
  saktan: 0,
};

function isoDay(offsetDays: number): string {
  return new Date((EPOCH + offsetDays * DAY) * 1000).toISOString().slice(0, 10);
}

export function demoPersonas(): PersonasPayload {
  const personas: PersonaSummary[] = PERSONA_NAMES.map((name, index) => {
    const runs = RUNS[name] ?? 0;
    const [provider, model] = MODELS[name] ?? ["huggingface", "unknown"];
    return {
      name,
      display_name: displayName(name),
      provider,
      model,
      // SakTan has never run in this sample: an idle persona is a real state,
      // and the UI must render it rather than hide it.
      has_shard: runs > 0,
      fact_count: runs * 3,
      observation_count: Math.floor(runs / 4),
      runs,
      errors: Math.floor(runs / 25),
      avg_latency_ms: 320 + index * 45,
      input_tokens: runs * 820,
      output_tokens: runs * 310,
      last_run_at: runs > 0 ? EPOCH - index * 900 : null,
    };
  });
  return { personas, unattributed_runs: 37 };
}

export function demoMetrics(): MetricsPayload {
  const trends: TrendPoint[] = Array.from({ length: 14 }, (_, i) => ({
    date: isoDay(i - 13),
    runs: 28 + ((i * 7) % 23),
    errors: i % 5 === 0 ? 2 : 1,
    avg_latency_ms: 300 + ((i * 31) % 180),
    input_tokens: 12_000 + i * 640,
    output_tokens: 4_100 + i * 210,
  }));
  const total = trends.reduce((sum, t) => sum + t.runs, 0);
  const inputTokens = trends.reduce((sum, t) => sum + t.input_tokens, 0);
  const outputTokens = trends.reduce((sum, t) => sum + t.output_tokens, 0);

  return {
    total_runs: total,
    error_rate: 0.021,
    avg_latency_ms: 388,
    tokens: {
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      total_tokens: inputTokens + outputTokens,
    },
    stop_reasons: { end_turn: total - 41, max_tokens: 29, tool_use: 12 },
    per_model: {
      "gemini-3.1-flash-lite": {
        count: 351,
        input_tokens: 288_000,
        output_tokens: 109_000,
        avg_latency_s: 0.34,
      },
      "Qwen/Qwen3-Coder-30B-A3B-Instruct": {
        count: 82,
        input_tokens: 67_000,
        output_tokens: 25_000,
        avg_latency_s: 0.62,
      },
      "DeepSeek-V4-Flash": {
        count: 46,
        input_tokens: 37_000,
        output_tokens: 14_000,
        avg_latency_s: 0.48,
      },
    },
    trends,
  };
}

const DEMO_TASKS = [
  "Summarise this week's session logs",
  "Draft the release notes for v2.1",
  "Audit the guardrail bypass regression tests",
  "Reconcile the persona skill counts on disk",
  "Check the HF dataset card metadata",
  "Consolidate duplicate memory facts",
  "Review the nightly eval trend",
  "Prepare the ServiceQuoteBot revenue rollup",
];

export function demoSessions(query?: { search?: string | null; limit?: number; offset?: number }) {
  const all: SessionSummary[] = DEMO_TASKS.map((task, i) => {
    const persona = i % 4 === 3 ? null : PERSONA_NAMES[i % PERSONA_NAMES.length];
    return {
      id: `${EPOCH - i * 1800}_demo${i.toString().padStart(4, "0")}`,
      timestamp: EPOCH - i * 1800,
      // Every fourth session is unattributed, mirroring a real log that
      // predates persona attribution.
      persona,
      task,
      model: persona ? (MODELS[persona]?.[1] ?? "unknown") : "claude-opus-4-8",
      iterations: 1 + (i % 4),
      stop_reason: i % 7 === 6 ? "max_tokens" : "end_turn",
      tokens: {
        input_tokens: 900 + i * 120,
        output_tokens: 300 + i * 40,
        total_tokens: 1200 + i * 160,
      },
      message_count: 2 + (i % 6),
      tool_call_count: i % 3,
      had_error: i % 8 === 7,
    };
  });

  const search = query?.search?.trim().toLowerCase();
  const filtered = search
    ? all.filter((s) => `${s.task} ${s.model} ${s.persona}`.toLowerCase().includes(search))
    : all;
  const offset = Math.max(0, query?.offset ?? 0);
  const limit = Math.min(100, Math.max(1, query?.limit ?? 20));

  const payload: SessionsPayload = {
    sessions: filtered.slice(offset, offset + limit),
    total: filtered.length,
    detail: null,
  };
  return payload;
}

function growth(start: number, step: number): GrowthSeries {
  const labels: string[] = [];
  const values: number[] = [];
  let running = start;
  for (let i = 0; i < 30; i += 1) {
    running += step + (i % 4);
    labels.push(isoDay(i - 29));
    values.push(running);
  }
  return { labels, values };
}

export function demoMemory(query?: { query?: string | null; limit?: number }): MemoryPayload {
  const facts: FactRecord[] = [
    ["preference", "theme", "Prefers a dark, low-contrast terminal"],
    ["profile", "location", "Based in Cork, Ireland"],
    ["note", null, "Nightly consolidation runs at 03:00 UTC"],
    ["preference", "tone", "Wants answers direct, without preamble"],
    ["note", null, "SakKing owns the coding-heavy workloads"],
    ["profile", "budget", "Every operation must stay zero-cost"],
  ].map(([kind, key, value], i) => ({
    id: i + 1,
    persona: PERSONA_NAMES[i % PERSONA_NAMES.length],
    kind: kind as string,
    key: key as string | null,
    value: value as string,
    tags: i % 2 === 0 ? ["core"] : [],
    created_at: EPOCH - i * 7200,
    updated_at: EPOCH - i * 3600,
  }));

  const observations: ObservationRecord[] = [
    "Works late into the evening most days",
    "Prefers plans reviewed before any code lands",
    "Reads test output closely and expects it quoted",
    "Treats stale documentation as a real defect",
  ].map((summary, i) => ({
    id: i + 1,
    persona: PERSONA_NAMES[i % PERSONA_NAMES.length],
    summary,
    weight: 2.5 - i * 0.3,
    confidence: 0.92 - i * 0.07,
    created_at: EPOCH - i * 10_800,
  }));

  const search = query?.query?.trim().toLowerCase();
  const limit = Math.min(500, Math.max(1, query?.limit ?? 100));

  return {
    facts: (search
      ? facts.filter((f) => `${f.kind} ${f.key} ${f.value}`.toLowerCase().includes(search))
      : facts
    ).slice(0, limit),
    observations: (search
      ? observations.filter((o) => o.summary.toLowerCase().includes(search))
      : observations
    ).slice(0, limit),
    total_facts: 412,
    total_observations: 87,
    facts_this_week: 23,
    observations_this_week: 6,
    fact_growth: growth(280, 4),
    observation_growth: growth(52, 1),
    kind_counts: { note: 198, preference: 96, profile: 71, lead: 31, revenue: 16 },
  };
}

export function demoAudit(query?: { severity?: string | null; limit?: number }): AuditPayload {
  const events: AuditEvent[] = [
    ["mcp_validation", "high", "Rejected an MCP server outside the allowlist"],
    ["symlink_detected", "medium", "Symlink encountered while resolving a read path"],
    ["env_pin", "low", "Environment fingerprint verified at startup"],
    ["shell_hardening", "critical", "Blocked a destructive shell command"],
    ["config_integrity", "low", "Config file checksum unchanged"],
    ["path_validation", "medium", "Denied a read outside the allowed roots"],
  ].map(([type, severity, message], i) => ({
    timestamp: EPOCH - i * 5400,
    type: type as string,
    severity: severity as string,
    message: message as string,
    details: { source: "demo" },
  }));

  const counts: Record<string, number> = {};
  for (const event of events) {
    counts[event.severity] = (counts[event.severity] ?? 0) + 1;
  }

  const wanted = query?.severity?.trim().toLowerCase();
  // An unknown severity narrows to nothing — it must not fall back to
  // returning everything, which is what the old reader did.
  const filtered = wanted ? events.filter((e) => e.severity.toLowerCase() === wanted) : events;
  const limit = Math.min(1000, Math.max(1, query?.limit ?? 200));

  return {
    events: filtered.slice(0, limit),
    severity_counts: counts,
    total: filtered.length,
  };
}

export function demoWorkflows(limit = 100): WorkflowsPayload {
  const runs: WorkflowRunSummary[] = [
    ["nightly-consolidation", "completed", 6, 0],
    ["hf-card-refresh", "completed", 4, 0],
    ["eval-sweep", "failed", 5, 1],
    ["persona-skill-audit", "running", 3, 0],
  ].map(([name, status, steps, failed], i) => {
    const started = new Date((EPOCH - i * 21_600) * 1000).toISOString();
    const running = status === "running";
    return {
      run_id: `demo-run-${i + 1}`,
      workflow_name: name as string,
      status: status as string,
      started_at: started,
      finished_at: running ? null : new Date((EPOCH - i * 21_600 + 95) * 1000).toISOString(),
      duration_seconds: running ? null : 95,
      step_count: steps as number,
      failed_steps: failed as number,
    };
  });
  return { runs: runs.slice(0, Math.min(500, Math.max(1, limit))) };
}
