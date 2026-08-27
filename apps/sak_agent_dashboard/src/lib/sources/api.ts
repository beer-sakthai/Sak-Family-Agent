/**
 * Reads through the Python HTTP API (`sakthai web serve`).
 *
 * This is the hosted case: a deploy has no `~/.sakthai/`, so it talks to a
 * reachable SakThai server instead. Selected by setting `SAKTHAI_API_URL`.
 *
 * The API returns the same envelopes this file unwraps, generated from the same
 * `web/contracts.py`, so there is no translation layer here — just transport.
 */

import type {
  ApiEnvelope,
  AuditPayload,
  MemoryPayload,
  MetricsPayload,
  PersonasPayload,
  SessionsPayload,
  WorkflowRunDetail,
  WorkflowsPayload,
} from "../contracts.generated";
import type { AuditQuery, DashboardSource, MemoryQuery, SessionQuery } from "../source";

/** Requests are cheap and local-ish; a short timeout beats a hung route. */
const TIMEOUT_MS = 10_000;

export class ApiSource implements DashboardSource {
  readonly kind = "api" as const;

  constructor(
    private readonly baseUrl: string,
    private readonly token?: string,
  ) {}

  private async fetchJson<T>(pathname: string, params: Record<string, unknown> = {}): Promise<T> {
    const url = new URL(pathname, this.baseUrl.endsWith("/") ? this.baseUrl : `${this.baseUrl}/`);
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }

    const headers: Record<string, string> = { Accept: "application/json" };
    if (this.token) headers.Authorization = `Bearer ${this.token}`;

    const response = await fetch(url, {
      headers,
      signal: AbortSignal.timeout(TIMEOUT_MS),
      // Always hit the server: this is live agent state, not a static asset.
      cache: "no-store",
    });

    if (!response.ok) {
      // 401/403 almost always means SAKTHAI_API_TOKEN is missing or stale, so
      // say that rather than surfacing a bare status code.
      const hint =
        response.status === 401 || response.status === 403
          ? " (check SAKTHAI_API_TOKEN — get one from `sakthai web setup`)"
          : "";
      throw new Error(`SakThai API ${response.status} for ${pathname}${hint}`);
    }

    const body = (await response.json()) as ApiEnvelope<T>;
    return body.data;
  }

  getPersonas(): Promise<PersonasPayload> {
    return this.fetchJson<PersonasPayload>("api/personas");
  }

  getMetrics(limit?: number): Promise<MetricsPayload> {
    return this.fetchJson<MetricsPayload>("api/metrics", { limit });
  }

  getSessions(query?: SessionQuery): Promise<SessionsPayload> {
    return this.fetchJson<SessionsPayload>("api/sessions", {
      search: query?.search,
      limit: query?.limit,
      offset: query?.offset,
      id: query?.id,
    });
  }

  getMemory(query?: MemoryQuery): Promise<MemoryPayload> {
    return this.fetchJson<MemoryPayload>("api/memory", {
      query: query?.query,
      limit: query?.limit,
    });
  }

  getAudit(query?: AuditQuery): Promise<AuditPayload> {
    return this.fetchJson<AuditPayload>("api/audit", {
      severity: query?.severity,
      limit: query?.limit,
    });
  }

  getWorkflows(limit?: number): Promise<WorkflowsPayload> {
    return this.fetchJson<WorkflowsPayload>("api/workflows", { limit });
  }

  getWorkflow(runId: string): Promise<WorkflowRunDetail | null> {
    return this.fetchJson<WorkflowRunDetail | null>("api/workflows", { id: runId });
  }
}
