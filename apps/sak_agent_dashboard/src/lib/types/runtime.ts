/**
 * types/runtime.ts — Core runtime types: agents, metrics, memory, sessions.
 *
 * Moved from the monolithic types.ts. Imported via the `@/lib/types` barrel
 * (`types/index.ts`), which re-exports everything here.
 */

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
