/**
 * The one seam every dashboard route reads through.
 *
 * The dashboard has to work in two environments that share no filesystem: a
 * developer's machine, where `~/.sakthai/` is right there, and a hosted deploy,
 * where it does not exist. Rather than sprinkling fallbacks through the route
 * handlers, there is one interface with three implementations and one rule for
 * picking between them.
 *
 * The important property is that **every response says which source produced
 * it**. What this replaces was a blanket `try/catch → demo data` in all four
 * routes, which is how a broken SQLite import ended up serving plausible fake
 * memory data indefinitely with nothing to indicate it.
 */

import {
  PERSONA_NAMES,
  type ApiEnvelope,
  type AuditPayload,
  type DataSource,
  type MemoryPayload,
  type MetricsPayload,
  type PersonasPayload,
  type SessionsPayload,
  type WorkflowRunDetail,
  type WorkflowsPayload,
} from "./contracts.generated";

export interface SessionQuery {
  search?: string | null;
  limit?: number;
  offset?: number;
  id?: string | null;
  /** Narrow to these personas. Null/absent means the whole family. */
  personas?: string[] | null;
}

export interface MemoryQuery {
  query?: string | null;
  limit?: number;
  /** Narrow to these personas' own shards. Null/absent means the whole family. */
  personas?: string[] | null;
}

export interface AuditQuery {
  severity?: string | null;
  limit?: number;
  /**
   * Narrow to the logs under these personas' own roots. An AuditEvent carries
   * no persona of its own, so the attribution is positional: only that
   * persona's process writes to that root.
   */
  personas?: string[] | null;
}

export interface MetricsQuery {
  limit?: number;
  /** Narrow to these personas' runs. Null/absent means the whole family. */
  personas?: string[] | null;
}

/** Everything a dashboard route can ask for, independent of where it comes from. */
export interface DashboardSource {
  readonly kind: DataSource;
  getPersonas(): Promise<PersonasPayload>;
  getMetrics(query?: MetricsQuery): Promise<MetricsPayload>;
  getSessions(query?: SessionQuery): Promise<SessionsPayload>;
  getMemory(query?: MemoryQuery): Promise<MemoryPayload>;
  getAudit(query?: AuditQuery): Promise<AuditPayload>;
  getWorkflows(limit?: number): Promise<WorkflowsPayload>;
  getWorkflow(runId: string): Promise<WorkflowRunDetail | null>;
}

/** Wrap a payload in the same envelope shape the Python API returns. */
export function envelope<T>(data: T, source: DataSource): ApiEnvelope<T> {
  return {
    ok: true,
    source,
    generated_at: new Date().toISOString(),
    data,
  };
}

/** Clamp a query-string integer. Returns the fallback for anything unusable. */
export function intParam(
  raw: string | null | undefined,
  fallback: number,
  min: number,
  max: number,
): number {
  if (raw === null || raw === undefined || raw.trim() === "") return fallback;
  const parsed = Number.parseInt(raw, 10);
  // `Number.parseInt("abc")` is NaN, and `Math.max(1, NaN)` is NaN — which is
  // how `?limit=abc` used to reach `slice(0, NaN)` and silently return an
  // empty page with a 200. Fall back instead.
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, parsed));
}

/**
 * Narrow a `persona=` query value to known persona names.
 *
 * Mirrors `web/api.py:parse_personas`, deliberately including its fallback:
 * a value naming no persona we know yields null — the whole family — rather
 * than an empty list, which would render as "this persona has nothing"
 * when the truth is that the filter was unreadable.
 */
export function parsePersonas(raw: string | null | undefined): string[] | null {
  if (!raw || raw.trim() === "") return null;
  const wanted = new Set(raw.split(",").map((part) => part.trim().toLowerCase()));
  const known = PERSONA_NAMES.filter((name) => wanted.has(name));
  return known.length > 0 ? [...known] : null;
}

/**
 * Pick a source for one request, in order:
 *
 *  1. an explicit `?demo=1` — the user asked for sample data
 *  2. `SAKTHAI_API_URL` set — talk to the Python API (the hosted case)
 *  3. otherwise the local filesystem, degrading to demo **only** when the
 *     runtime directory genuinely is not there
 *
 * Imports are dynamic so a deploy that only ever uses `ApiSource` never loads
 * `better-sqlite3`, and the browser bundle never sees `fs` at all.
 */
export async function resolveSource(request: Request): Promise<DashboardSource> {
  const params = new URL(request.url).searchParams;
  const demoRequested = params.get("demo") === "true" || params.get("demo") === "1";

  if (demoRequested) {
    const { DemoSource } = await import("./sources/demo");
    return new DemoSource();
  }

  const apiUrl = process.env.SAKTHAI_API_URL;
  if (apiUrl && apiUrl.trim().length > 0) {
    const { ApiSource } = await import("./sources/api");
    return new ApiSource(apiUrl.trim(), process.env.SAKTHAI_API_TOKEN);
  }

  const { runtimeAvailable } = await import("./runtime");
  if (!runtimeAvailable()) {
    const { DemoSource } = await import("./sources/demo");
    return new DemoSource();
  }

  const { LocalFsSource } = await import("./sources/local");
  return new LocalFsSource();
}

/**
 * Run one source call and envelope it, turning a thrown error into a 500.
 *
 * Deliberately does *not* fall back to demo data: a source that fails should
 * say so, not quietly substitute fiction.
 */
export async function respond<T>(
  request: Request,
  call: (source: DashboardSource) => Promise<T>,
): Promise<Response> {
  try {
    const source = await resolveSource(request);
    const data = await call(source);
    return Response.json(envelope(data, source.kind));
  } catch (error) {
    console.error("Dashboard API request failed:", error);
    return Response.json(
      { ok: false, error: "InternalError", message: "Failed to build payload" },
      { status: 500 },
    );
  }
}
