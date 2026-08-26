/**
 * Reads `~/.sakthai/` directly from disk.
 *
 * The local-development case: the runtime state is right there, so going
 * through HTTP would only add a hop and a server to start. This mirrors
 * `sakthai/web/api.py` — same roots, same attribution rules, same clamping —
 * and both are checked against the same generated contract.
 *
 * Attribution, specifically: a record's own `persona` field wins; failing that,
 * a log found under a persona's own root belongs to that persona, because only
 * that persona's process writes there; failing both, it is unattributed. What
 * this replaces guessed from model-name substrings and then fell back to
 * `index % 5` round-robin over a hardcoded list of five personas.
 */

import fs from "fs";
import path from "path";

import {
  PERSONA_NAMES,
  type AuditEvent,
  type AuditPayload,
  type FactRecord,
  type GrowthSeries,
  type MemoryPayload,
  type MetricsPayload,
  type ModelUsage,
  type ObservationRecord,
  type PersonaSummary,
  type PersonasPayload,
  type SessionDetail,
  type SessionSummary,
  type SessionsPayload,
  type TokenStats,
  type TrendPoint,
  type WorkflowRunDetail,
  type WorkflowRunSummary,
  type WorkflowsPayload,
} from "../contracts.generated";
import { displayName, runtimeRoots, sakthaiHome } from "../runtime";
import type { AuditQuery, DashboardSource, MemoryQuery, SessionQuery } from "../source";

/** Matches `web/api.py:MAX_SESSION_SCAN`. */
const MAX_SESSION_SCAN = 500;
const MAX_AUDIT_LINES = 2000;
const EVAL_WINDOW = 2000;

/** Ids reaching a path join must be pattern-checked first. */
const SAFE_ID = /^[A-Za-z0-9_.-]+$/;

interface EvalRecord {
  timestamp?: number;
  model?: string;
  provider?: string;
  stop_reason?: string;
  latency_s?: number;
  input_tokens?: number;
  output_tokens?: number;
  had_error?: boolean;
  persona?: string | null;
}

function readJsonl(file: string, maxLines: number): Record<string, unknown>[] {
  let raw: string;
  try {
    raw = fs.readFileSync(file, "utf8");
  } catch {
    return [];
  }
  const lines = raw.split("\n").slice(-maxLines);
  const out: Record<string, unknown>[] = [];
  for (const line of lines) {
    if (!line.trim()) continue;
    try {
      const parsed: unknown = JSON.parse(line);
      // A torn final line is normal in a log an agent appends to live.
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        out.push(parsed as Record<string, unknown>);
      }
    } catch {
      continue;
    }
  }
  return out;
}

function readJson(file: string): Record<string, unknown> | null {
  try {
    const parsed: unknown = JSON.parse(fs.readFileSync(file, "utf8"));
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
  } catch {
    return null;
  }
  return null;
}

function asDict(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function num(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function str(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

/** Every eval record across every root, paired with its attributed persona. */
function evalRecordsWithAttribution(home: string): [EvalRecord, string | null][] {
  const out: [EvalRecord, string | null][] = [];
  for (const root of runtimeRoots(home)) {
    for (const raw of readJsonl(path.join(root.path, "eval.jsonl"), EVAL_WINDOW)) {
      const record = raw as EvalRecord;
      const attributed = record.persona || root.persona;
      out.push([record, typeof attributed === "string" ? attributed : null]);
    }
  }
  return out;
}

/**
 * A tiny mtime-keyed cache over the session directory listing.
 *
 * Every request used to `readdirSync` + `readFileSync` + `JSON.parse` every
 * file in `~/.sakthai/sessions/`, synchronously, blocking the event loop. The
 * key is the set of directory mtimes, so a new session invalidates it
 * immediately while repeated reads of an unchanged directory are free.
 */
let sessionCache: { key: string; summaries: SessionSummary[] } | null = null;

function sessionDirs(home: string): { dir: string; persona: string | null }[] {
  return runtimeRoots(home)
    .map((root) => ({ dir: path.join(root.path, "sessions"), persona: root.persona }))
    .filter(({ dir }) => {
      try {
        return fs.statSync(dir).isDirectory();
      } catch {
        return false;
      }
    });
}

function cacheKey(dirs: { dir: string }[]): string {
  return dirs
    .map(({ dir }) => {
      try {
        return `${dir}:${fs.statSync(dir).mtimeMs}`;
      } catch {
        return `${dir}:0`;
      }
    })
    .join("|");
}

function sessionSummary(
  id: string,
  data: Record<string, unknown>,
  fallbackPersona: string | null,
): SessionSummary {
  const result = asDict(data.result);
  const usage = asDict(data.usage);
  const toolCalls = Array.isArray(result.tool_calls) ? result.tool_calls : [];
  const messages = Array.isArray(data.messages) ? data.messages : [];
  const persona = typeof data.persona === "string" ? data.persona : fallbackPersona;

  const inputTokens = num(usage.input_tokens);
  const outputTokens = num(usage.output_tokens);
  const tokens: TokenStats = {
    input_tokens: inputTokens,
    output_tokens: outputTokens,
    total_tokens: num(usage.total_tokens) || inputTokens + outputTokens,
  };

  return {
    id,
    timestamp: num(data.timestamp),
    persona,
    task: str(data.task),
    model: str(data.model),
    iterations: num(result.iterations),
    stop_reason: str(result.stop_reason),
    tokens,
    message_count: messages.length,
    tool_call_count: toolCalls.length,
    had_error: toolCalls.some((call) => asDict(call).is_error === true),
  };
}

function flattenContent(content: unknown): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((block) => {
        if (block && typeof block === "object") {
          const b = asDict(block);
          return str(b.text) || str(b.name) || str(b.type);
        }
        return String(block);
      })
      .filter(Boolean)
      .join("\n");
  }
  return content === null || content === undefined ? "" : String(content);
}

function loadSessions(home: string): SessionSummary[] {
  const dirs = sessionDirs(home);
  const key = cacheKey(dirs);
  if (sessionCache && sessionCache.key === key) return sessionCache.summaries;

  const files: { file: string; stem: string; persona: string | null }[] = [];
  for (const { dir, persona } of dirs) {
    let entries: string[];
    try {
      entries = fs.readdirSync(dir);
    } catch {
      continue;
    }
    for (const entry of entries) {
      if (!entry.endsWith(".json")) continue;
      files.push({ file: path.join(dir, entry), stem: entry.slice(0, -5), persona });
    }
  }
  // Filenames are `<unix_seconds>_<uuid>`, so a reverse sort is chronological.
  files.sort((a, b) => (a.stem < b.stem ? 1 : a.stem > b.stem ? -1 : 0));

  const summaries: SessionSummary[] = [];
  for (const { file, stem, persona } of files.slice(0, MAX_SESSION_SCAN)) {
    const data = readJson(file);
    if (data) summaries.push(sessionSummary(stem, data, persona));
  }

  sessionCache = { key, summaries };
  return summaries;
}

/** Exposed so tests can force a cold read. */
export function clearSessionCache(): void {
  sessionCache = null;
}

function growthFrom(bins: number[], beforeStart: number, startTs: number): GrowthSeries {
  const labels: string[] = [];
  const values: number[] = [];
  let running = beforeStart;
  bins.forEach((count, index) => {
    running += count;
    labels.push(new Date((startTs + index * 86_400) * 1000).toISOString().slice(0, 10));
    values.push(running);
  });
  return { labels, values };
}

export class LocalFsSource implements DashboardSource {
  readonly kind = "local" as const;

  constructor(private readonly home: string = sakthaiHome()) {}

  async getPersonas(): Promise<PersonasPayload> {
    const { openDb } = await import("../db");

    const summaries = new Map<string, PersonaSummary>();
    for (const name of PERSONA_NAMES) {
      summaries.set(name, {
        name,
        display_name: displayName(name),
        provider: "",
        model: "",
        has_shard: false,
        fact_count: 0,
        observation_count: 0,
        runs: 0,
        errors: 0,
        avg_latency_ms: 0,
        input_tokens: 0,
        output_tokens: 0,
        last_run_at: null,
      });
    }

    for (const name of PERSONA_NAMES) {
      const counts = openDb(path.join(this.home, name, "memory.db"), (db) => ({
        facts: num(db.prepare("SELECT COUNT(*) AS n FROM facts").get()?.n),
        observations: num(db.prepare("SELECT COUNT(*) AS n FROM observations").get()?.n),
      }));
      if (!counts) continue;
      const entry = summaries.get(name)!;
      entry.has_shard = true;
      entry.fact_count = counts.facts;
      entry.observation_count = counts.observations;
    }

    const latency = new Map<string, number>();
    let unattributed = 0;
    for (const [record, persona] of evalRecordsWithAttribution(this.home)) {
      if (!persona || !summaries.has(persona)) {
        unattributed += 1;
        continue;
      }
      const entry = summaries.get(persona)!;
      entry.runs += 1;
      entry.errors += record.had_error ? 1 : 0;
      entry.input_tokens += num(record.input_tokens);
      entry.output_tokens += num(record.output_tokens);
      latency.set(persona, (latency.get(persona) ?? 0) + num(record.latency_s));
      if (typeof record.timestamp === "number") {
        entry.last_run_at =
          entry.last_run_at === null
            ? record.timestamp
            : Math.max(entry.last_run_at, record.timestamp);
      }
    }

    for (const [name, entry] of summaries) {
      if (entry.runs > 0) {
        entry.avg_latency_ms =
          Math.round(((latency.get(name) ?? 0) / entry.runs) * 1000 * 100) / 100;
      }
    }

    return {
      personas: PERSONA_NAMES.map((name) => summaries.get(name)!),
      unattributed_runs: unattributed,
    };
  }

  async getMetrics(limit = EVAL_WINDOW): Promise<MetricsPayload> {
    const records = evalRecordsWithAttribution(this.home)
      .map(([record]) => record)
      .slice(-Math.max(1, limit));

    const tokens: TokenStats = { input_tokens: 0, output_tokens: 0, total_tokens: 0 };
    if (records.length === 0) {
      return {
        total_runs: 0,
        error_rate: 0,
        avg_latency_ms: 0,
        tokens,
        stop_reasons: {},
        per_model: {},
        trends: [],
      };
    }

    const perModel: Record<string, ModelUsage> = {};
    const modelLatency: Record<string, number> = {};
    const stopReasons: Record<string, number> = {};
    const days = new Map<string, TrendPoint>();
    const dayLatency = new Map<string, number>();
    let errors = 0;
    let totalLatency = 0;

    for (const record of records) {
      const model = record.model || "unknown";
      const usage = (perModel[model] ??= {
        count: 0,
        input_tokens: 0,
        output_tokens: 0,
        avg_latency_s: 0,
      });
      usage.count += 1;
      usage.input_tokens += num(record.input_tokens);
      usage.output_tokens += num(record.output_tokens);
      modelLatency[model] = (modelLatency[model] ?? 0) + num(record.latency_s);

      const reason = record.stop_reason || "unknown";
      stopReasons[reason] = (stopReasons[reason] ?? 0) + 1;

      errors += record.had_error ? 1 : 0;
      totalLatency += num(record.latency_s);
      tokens.input_tokens += num(record.input_tokens);
      tokens.output_tokens += num(record.output_tokens);

      if (typeof record.timestamp === "number") {
        const date = new Date(record.timestamp * 1000).toISOString().slice(0, 10);
        const point =
          days.get(date) ??
          ({
            date,
            runs: 0,
            errors: 0,
            avg_latency_ms: 0,
            input_tokens: 0,
            output_tokens: 0,
          } as TrendPoint);
        point.runs += 1;
        point.errors += record.had_error ? 1 : 0;
        point.input_tokens += num(record.input_tokens);
        point.output_tokens += num(record.output_tokens);
        days.set(date, point);
        dayLatency.set(date, (dayLatency.get(date) ?? 0) + num(record.latency_s));
      }
    }

    tokens.total_tokens = tokens.input_tokens + tokens.output_tokens;
    for (const [model, usage] of Object.entries(perModel)) {
      usage.avg_latency_s = Math.round(((modelLatency[model] ?? 0) / usage.count) * 1000) / 1000;
    }
    for (const [date, point] of days) {
      point.avg_latency_ms =
        Math.round(((dayLatency.get(date) ?? 0) / point.runs) * 1000 * 100) / 100;
    }

    return {
      total_runs: records.length,
      error_rate: Math.round((errors / records.length) * 10_000) / 10_000,
      avg_latency_ms: Math.round((totalLatency / records.length) * 1000 * 100) / 100,
      tokens,
      stop_reasons: stopReasons,
      per_model: perModel,
      trends: [...days.keys()].sort().map((date) => days.get(date)!),
    };
  }

  async getSessions(query?: SessionQuery): Promise<SessionsPayload> {
    const limit = Math.min(100, Math.max(1, query?.limit ?? 20));
    const offset = Math.max(0, query?.offset ?? 0);

    let summaries = loadSessions(this.home);
    const search = query?.search?.trim().toLowerCase();
    if (search) {
      const terms = search.split(/\s+/);
      summaries = summaries.filter((s) => {
        const haystack = `${s.id} ${s.task} ${s.model} ${s.persona}`.toLowerCase();
        return terms.every((term) => haystack.includes(term));
      });
    }

    return {
      sessions: summaries.slice(offset, offset + limit),
      total: summaries.length,
      detail: query?.id ? await this.getSessionDetail(query.id) : null,
    };
  }

  async getSessionDetail(sessionId: string): Promise<SessionDetail | null> {
    if (!SAFE_ID.test(sessionId)) return null;
    for (const { dir, persona } of sessionDirs(this.home)) {
      const file = path.join(dir, `${sessionId}.json`);
      if (!fs.existsSync(file)) continue;
      const data = readJson(file);
      if (!data) return null;
      const result = asDict(data.result);
      const rawMessages = Array.isArray(data.messages) ? data.messages : [];
      return {
        summary: sessionSummary(sessionId, data, persona),
        messages: rawMessages
          .filter((m) => m && typeof m === "object" && !Array.isArray(m))
          .map((m) => ({
            role: str(asDict(m).role),
            content: flattenContent(asDict(m).content),
          })),
        result_text: str(result.text),
        tool_calls: (Array.isArray(result.tool_calls) ? result.tool_calls : [])
          .filter((c) => c && typeof c === "object")
          .map((c) => ({ name: str(asDict(c).name), is_error: asDict(c).is_error === true })),
      };
    }
    return null;
  }

  async getMemory(query?: MemoryQuery): Promise<MemoryPayload> {
    const { openDb } = await import("../db");
    const limit = Math.min(500, Math.max(1, query?.limit ?? 100));
    const now = Math.floor(Date.now() / 1000);
    const startTs = now - 30 * 86_400;
    const weekAgo = now - 7 * 86_400;

    const shards: { persona: string; file: string }[] = [
      ...PERSONA_NAMES.map((persona) => ({
        persona,
        file: path.join(this.home, persona, "memory.db"),
      })),
      { persona: "shared", file: path.join(this.home, "memory.db") },
    ];

    const facts: FactRecord[] = [];
    const observations: ObservationRecord[] = [];
    let totalFacts = 0;
    let totalObservations = 0;
    let factsThisWeek = 0;
    let observationsThisWeek = 0;
    const factBins = new Array<number>(30).fill(0);
    const obsBins = new Array<number>(30).fill(0);
    let factsBefore = 0;
    let obsBefore = 0;
    const kindCounts: Record<string, number> = {};

    const search = query?.query?.trim().toLowerCase();

    for (const { persona, file } of shards) {
      const read = openDb(file, (db) => {
        const factRows = db.prepare("SELECT * FROM facts ORDER BY updated_at DESC").all();
        const obsRows = db.prepare("SELECT * FROM observations ORDER BY weight DESC").all();
        return { factRows, obsRows };
      });
      if (!read) continue;

      for (const row of read.factRows) {
        const r = asDict(row);
        const createdAt = num(r.created_at);
        totalFacts += 1;
        if (createdAt >= weekAgo) factsThisWeek += 1;
        if (createdAt <= startTs) factsBefore += 1;
        else {
          const bin = Math.floor((createdAt - startTs) / 86_400);
          if (bin >= 0 && bin < 30) factBins[bin] += 1;
        }
        const kind = str(r.kind, "note");
        kindCounts[kind] = (kindCounts[kind] ?? 0) + 1;

        let tags: string[] = [];
        try {
          const parsed: unknown = r.tags ? JSON.parse(String(r.tags)) : [];
          if (Array.isArray(parsed)) tags = parsed.map(String);
        } catch {
          tags = [];
        }

        const record: FactRecord = {
          id: num(r.id),
          persona,
          kind,
          key: typeof r.key === "string" ? r.key : null,
          value: str(r.value),
          tags,
          created_at: createdAt,
          updated_at: num(r.updated_at),
        };
        if (!search || `${record.kind} ${record.key} ${record.value}`.toLowerCase().includes(search)) {
          facts.push(record);
        }
      }

      for (const row of read.obsRows) {
        const r = asDict(row);
        const createdAt = num(r.created_at);
        totalObservations += 1;
        if (createdAt >= weekAgo) observationsThisWeek += 1;
        if (createdAt <= startTs) obsBefore += 1;
        else {
          const bin = Math.floor((createdAt - startTs) / 86_400);
          if (bin >= 0 && bin < 30) obsBins[bin] += 1;
        }
        const record: ObservationRecord = {
          id: num(r.id),
          persona,
          summary: str(r.summary),
          weight: num(r.weight),
          confidence: num(r.confidence),
          created_at: createdAt,
        };
        if (!search || record.summary.toLowerCase().includes(search)) observations.push(record);
      }
    }

    facts.sort((a, b) => b.updated_at - a.updated_at);
    observations.sort((a, b) => b.weight - a.weight);

    return {
      facts: facts.slice(0, limit),
      observations: observations.slice(0, limit),
      total_facts: totalFacts,
      total_observations: totalObservations,
      facts_this_week: factsThisWeek,
      observations_this_week: observationsThisWeek,
      fact_growth: growthFrom(factBins, factsBefore, startTs),
      observation_growth: growthFrom(obsBins, obsBefore, startTs),
      kind_counts: kindCounts,
    };
  }

  async getAudit(query?: AuditQuery): Promise<AuditPayload> {
    const limit = Math.min(1000, Math.max(1, query?.limit ?? 200));
    const events: AuditEvent[] = [];
    for (const root of runtimeRoots(this.home)) {
      for (const raw of readJsonl(path.join(root.path, "audit.log"), MAX_AUDIT_LINES)) {
        events.push({
          timestamp: num(raw.timestamp),
          type: str(raw.type),
          severity: str(raw.severity, "low") || "low",
          message: str(raw.message),
          details: asDict(raw.details),
        });
      }
    }

    const counts: Record<string, number> = {};
    for (const event of events) {
      counts[event.severity] = (counts[event.severity] ?? 0) + 1;
    }

    const wanted = query?.severity?.trim().toLowerCase();
    // An unknown severity narrows to nothing, rather than falling back to
    // returning every event as the previous reader did.
    const filtered = wanted ? events.filter((e) => e.severity.toLowerCase() === wanted) : events;
    filtered.sort((a, b) => b.timestamp - a.timestamp);

    return { events: filtered.slice(0, limit), severity_counts: counts, total: filtered.length };
  }

  private workflowDir(): string {
    return path.join(this.home, "workflow_runs");
  }

  private workflowSummary(runId: string, data: Record<string, unknown>): WorkflowRunSummary {
    const steps = asDict(data.step_results);
    const started = typeof data.start_time === "string" ? data.start_time : null;
    const finished = typeof data.end_time === "string" ? data.end_time : null;
    return {
      run_id: runId,
      workflow_name: str(data.workflow_name),
      // RunStatus/StepStatus serialise UPPERCASE; lowercased for one form.
      status: str(data.status).toLowerCase(),
      started_at: started,
      finished_at: finished,
      duration_seconds: durationSeconds(started, finished),
      step_count: Object.keys(steps).length,
      failed_steps: Object.values(steps).filter(
        (step) => str(asDict(step).status).toLowerCase() === "failed",
      ).length,
    };
  }

  async getWorkflows(limit = 100): Promise<WorkflowsPayload> {
    const dir = this.workflowDir();
    let entries: string[];
    try {
      entries = fs.readdirSync(dir);
    } catch {
      return { runs: [] };
    }

    const runs: WorkflowRunSummary[] = [];
    for (const entry of entries) {
      if (!entry.endsWith(".json")) continue;
      const data = readJson(path.join(dir, entry));
      if (data) runs.push(this.workflowSummary(entry.slice(0, -5), data));
    }
    runs.sort((a, b) => (a.started_at ?? "").localeCompare(b.started_at ?? "") * -1);
    return { runs: runs.slice(0, Math.min(500, Math.max(1, limit))) };
  }

  async getWorkflow(runId: string): Promise<WorkflowRunDetail | null> {
    if (!SAFE_ID.test(runId)) return null;
    const data = readJson(path.join(this.workflowDir(), `${runId}.json`));
    if (!data) return null;
    const steps = asDict(data.step_results);
    return {
      summary: this.workflowSummary(runId, data),
      steps: Object.values(steps).map((raw) => {
        const step = asDict(raw);
        const started = typeof step.start_time === "string" ? step.start_time : null;
        const finished = typeof step.end_time === "string" ? step.end_time : null;
        return {
          step_id: str(step.step_id),
          status: str(step.status).toLowerCase(),
          attempts: num(step.attempts),
          error: typeof step.error === "string" ? step.error : null,
          started_at: started,
          finished_at: finished,
          duration_seconds: durationSeconds(started, finished),
        };
      }),
    };
  }
}

function durationSeconds(started: string | null, finished: string | null): number | null {
  if (!started || !finished) return null;
  const start = Date.parse(started);
  const end = Date.parse(finished);
  if (!Number.isFinite(start) || !Number.isFinite(end)) return null;
  return Math.max(0, (end - start) / 1000);
}
