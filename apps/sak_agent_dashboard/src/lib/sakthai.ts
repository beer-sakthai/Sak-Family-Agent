import fs from "fs";
import path from "path";
import os from "os";
import {
  AgentPersona,
  MetricsData,
  AuditLog,
  SessionMeta,
  SessionTranscript,
  AuditSeverity,
  SessionMessage,
  DataSource,
} from "./types";
import { PERSONAS, UNATTRIBUTED, personaName, resolvePersonaSlug } from "./personas";
import {
  DataSourceStrategy,
  SourceReadError,
  SourceUnavailableError,
  resolveDataSource,
} from "./dataSource";

const SAKTHAI_DIR = process.env.SAKTHAI_DIR || path.join(os.homedir(), ".sakthai");
const EVAL_FILE = path.join(SAKTHAI_DIR, "eval.jsonl");
const AUDIT_FILE = path.join(SAKTHAI_DIR, "audit.log");
const SESSIONS_DIR = path.join(SAKTHAI_DIR, "sessions");

/**
 * Demo generators live in `lib/demoData.ts` so the client shell can import the
 * same figures without pulling `fs` into the browser bundle. Re-exported here
 * to keep the existing `@/lib/sakthai` import sites working.
 */
import {
  getDemoAgents,
  getDemoMetrics,
  getDemoAuditLogs,
  getDemoSessions,
  DEMO_TOTAL_RUNS,
} from "./demoData";

export { getDemoAgents, getDemoMetrics, getDemoAuditLogs, getDemoSessions, DEMO_TOTAL_RUNS };

/** The synthetic row shown when runs cannot be attributed to any persona. */
function unattributedRow(runs: number, latencyMs: number): AgentPersona {
  return {
    slug: UNATTRIBUTED,
    name: "Unattributed",
    role: "Runs with no persona field",
    status: "Unknown",
    model: "\u2014",
    runs,
    latencyMs,
    skills: [],
    badge: "Unattributed",
    unattributed: true,
  };
}

export interface AgentOverviewResult {
  agents: AgentPersona[];
  dataSource: DataSource;
  /** Runs in eval.jsonl that carried no usable persona field. */
  unattributedRuns: number;
}

interface AgentOverviewData {
  agents: AgentPersona[];
  unattributedRuns: number;
}

export async function getAgentOverview(demo?: boolean): Promise<AgentOverviewResult> {
  const strategy: DataSourceStrategy<AgentOverviewData> = {
    readDemo: () => ({ agents: getDemoAgents(), unattributedRuns: 0 }),

    readLive: async () => {
      if (!fs.existsSync(EVAL_FILE)) {
        // The source simply is not there. Reporting "unavailable" rather than
        // silently serving demo data is what stops an empty machine from
        // looking identical to a busy one.
        throw new SourceUnavailableError();
      }

      try {
        const fileContent = fs.readFileSync(EVAL_FILE, "utf8");
        const lines = fileContent.split("\n").filter((l) => l.trim().length > 0);

        // An existing but empty eval.jsonl is a live read of zero runs, not a
        // missing source — fall through and report the roster with zero counts.

        const stats = new Map<string, { runs: number; totalLatencyMs: number }>();
        for (const p of PERSONAS) stats.set(p.slug, { runs: 0, totalLatencyMs: 0 });
        stats.set(UNATTRIBUTED, { runs: 0, totalLatencyMs: 0 });

        for (const line of lines) {
          let entry: Record<string, unknown>;
          try {
            entry = JSON.parse(line);
          } catch {
            continue; // Safe skip on corrupt line.
          }
          // No index fallback: an entry we cannot attribute goes to the
          // unattributed bucket rather than being assigned to a persona at random.
          const slug = resolvePersonaSlug(entry) ?? UNATTRIBUTED;
          const bucket = stats.get(slug);
          if (!bucket) continue;
          bucket.runs += 1;
          const rawLatency = Number(entry.latency_s ?? entry.latencyMs ?? 0);
          bucket.totalLatencyMs += Math.round(
            Number.isFinite(rawLatency) ? rawLatency * 1000 : 0
          );
        }

        const agents: AgentPersona[] = PERSONAS.map((p) => {
          const s = stats.get(p.slug)!;
          return {
            slug: p.slug,
            name: p.name,
            role: p.role,
            // Status reflects observed activity, not a hard-coded literal.
            status: s.runs > 0 ? "Active" : "Idle",
            model: p.model,
            provider: p.provider,
            skills: [...p.skills],
            badge: p.badge,
            runs: s.runs,
            latencyMs: s.runs > 0 ? Math.round(s.totalLatencyMs / s.runs) : 0,
            // benchmarkScore is deliberately omitted: eval.jsonl carries no
            // benchmark, and the previous code spread a hard-coded score into
            // the live path where it read as measured.
          };
        });

        const un = stats.get(UNATTRIBUTED)!;
        if (un.runs > 0) {
          agents.push(
            unattributedRow(un.runs, Math.round(un.totalLatencyMs / un.runs))
          );
        }

        return { agents, unattributedRuns: un.runs };
      } catch (error) {
        if (error instanceof SourceUnavailableError) throw error;
        throw new SourceReadError(error instanceof Error ? error.message : String(error));
      }
    },
  };

  const { data, dataSource } = await resolveDataSource(strategy, !!demo);
  return { agents: data.agents, dataSource, unattributedRuns: data.unattributedRuns };
}

export interface MetricsResult {
  metrics: MetricsData;
  dataSource: DataSource;
}

const EMPTY_METRICS: MetricsData = {
  totalRuns: 0,
  avgLatencyMs: 0,
  successRate: 0,
  tokenStats: { totalTokens: 0, promptTokens: 0, completionTokens: 0 },
  stopReasons: {},
  trends: [],
};

export async function getMetricsSummary(demo?: boolean): Promise<MetricsResult> {
  const strategy: DataSourceStrategy<MetricsData> = {
    readDemo: () => getDemoMetrics(),

    readLive: async () => {
      if (!fs.existsSync(EVAL_FILE)) {
        throw new SourceUnavailableError();
      }

      try {
        const fileContent = fs.readFileSync(EVAL_FILE, "utf8");
        const lines = fileContent.split("\n").filter((l) => l.trim().length > 0);

        if (lines.length === 0) {
          return { ...EMPTY_METRICS };
        }

        let totalRuns = 0;
        let totalLatencyMs = 0;
        let successfulRuns = 0;
        let promptTokens = 0;
        let completionTokens = 0;
        const stopReasons: Record<string, number> = {};
        const trendsMap: Record<string, { runs: number; totalLatencyMs: number }> = {};

        lines.forEach((line) => {
          try {
            const entry = JSON.parse(line);
            totalRuns += 1;

            const latencyMs = Math.round((entry.latency_s || 0) * 1000);
            totalLatencyMs += latencyMs;

            if (!entry.had_error) {
              successfulRuns += 1;
            }

            const pTok = Number(entry.input_tokens || entry.prompt_tokens || 0);
            const cTok = Number(entry.output_tokens || entry.completion_tokens || 0);
            promptTokens += pTok;
            completionTokens += cTok;

            const reason = entry.stop_reason || "unknown";
            stopReasons[reason] = (stopReasons[reason] || 0) + 1;

            const ts = entry.timestamp ? new Date(entry.timestamp * 1000) : new Date();
            const dateStr = ts.toISOString().split("T")[0];
            if (!trendsMap[dateStr]) {
              trendsMap[dateStr] = { runs: 0, totalLatencyMs: 0 };
            }
            trendsMap[dateStr].runs += 1;
            trendsMap[dateStr].totalLatencyMs += latencyMs;
          } catch {
            // Skip malformed line
          }
        });

        if (totalRuns === 0) {
          return { ...EMPTY_METRICS };
        }

        const avgLatencyMs = Math.round(totalLatencyMs / totalRuns);
        const successRate = Number((successfulRuns / totalRuns).toFixed(3));
        const totalTokens = promptTokens + completionTokens;

        const trends = Object.entries(trendsMap)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([date, data]) => ({
            date,
            runs: data.runs,
            latencyMs: data.runs > 0 ? Math.round(data.totalLatencyMs / data.runs) : 0,
          }));

        return {
          totalRuns,
          avgLatencyMs,
          successRate,
          tokenStats: {
            totalTokens,
            promptTokens,
            completionTokens,
          },
          stopReasons,
          trends,
        };
      } catch (error) {
        if (error instanceof SourceUnavailableError) throw error;
        throw new SourceReadError(error instanceof Error ? error.message : String(error));
      }
    },
  };

  const { data, dataSource } = await resolveDataSource(strategy, !!demo);
  return { metrics: data, dataSource };
}

export interface AuditLogsResult {
  logs: AuditLog[];
  dataSource: DataSource;
}

export async function getAuditLogs(
  demo?: boolean,
  severityFilter?: string
): Promise<AuditLogsResult> {
  const validSeverities: AuditSeverity[] = ["info", "warning", "error", "critical"];

  const parseSeverity = (raw: string): AuditSeverity => {
    const s = String(raw || "").toLowerCase();
    if (s === "high" || s === "critical") return "critical";
    if (s === "medium" || s === "warning") return "warning";
    if (s === "error") return "error";
    return "info";
  };

  const strategy: DataSourceStrategy<AuditLog[]> = {
    readDemo: () => getDemoAuditLogs(),

    readLive: async () => {
      if (!fs.existsSync(AUDIT_FILE)) {
        throw new SourceUnavailableError();
      }

      try {
        const fileContent = fs.readFileSync(AUDIT_FILE, "utf8");
        const lines = fileContent.split("\n").filter((l) => l.trim().length > 0);

        return lines.map((line, idx) => {
          try {
            const entry = JSON.parse(line);
            const rawTs = entry.timestamp;
            const isoTs =
              typeof rawTs === "number" && rawTs > 0
                ? new Date(rawTs * 1000).toISOString()
                : typeof rawTs === "string"
                ? rawTs
                : new Date().toISOString();

            return {
              id: entry.id || idx + 1,
              timestamp: isoTs,
              persona: entry.persona || "SakSit",
              severity: parseSeverity(entry.severity),
              event: entry.type || entry.event || "Security Audit Event",
              details:
                entry.message ||
                (typeof entry.details === "string"
                  ? entry.details
                  : JSON.stringify(entry.details || {})),
            };
          } catch {
            return {
              id: idx + 1,
              timestamp: new Date().toISOString(),
              persona: "SakSit",
              severity: "info" as AuditSeverity,
              event: "Unparseable Audit Event",
              details: line,
            };
          }
        });
      } catch (error) {
        if (error instanceof SourceUnavailableError) throw error;
        throw new SourceReadError(error instanceof Error ? error.message : String(error));
      }
    },
  };

  const { data, dataSource } = await resolveDataSource(strategy, !!demo);
  let logs = data;

  if (severityFilter && severityFilter.trim().length > 0) {
    const filterLower = severityFilter.toLowerCase();
    if (validSeverities.includes(filterLower as AuditSeverity)) {
      logs = logs.filter((l) => l.severity === filterLower);
    }
    // Note: If severityFilter is invalid (e.g. "INVALID_SEVERITY_LEVEL"), return all logs unchanged per spec/tests
  }

  return { logs, dataSource };
}

export async function getSessionTranscripts(options?: {
  demo?: boolean;
  search?: string;
  limit?: number;
  offset?: number;
  id?: string;
}): Promise<{
  sessions: SessionMeta[];
  total: number;
  detail?: SessionTranscript;
  dataSource: DataSource;
}> {
  const limit = Math.min(100, Math.max(1, Math.floor(options?.limit ?? 20)));
  const offset = Math.max(0, Math.floor(options?.offset ?? 0));
  const search = options?.search ? options.search.trim().toLowerCase() : "";
  const targetId = options?.id ? options.id.trim() : null;

  // Both the "unavailable" (no sessions dir) and the "demo" (read failure on
  // an existing dir) fallbacks previously produced demo data — the original
  // code just built two visibly different shapes for it (one enriched with
  // task/model/messages/result, one a bare SessionMeta spread). Since neither
  // shape difference was load-bearing (the trimmed `sessions` page below never
  // includes those fields, and no test exercises a readdirSync failure), the
  // Strategy migration unifies both fallbacks onto the one enriched demo
  // reader below rather than keeping the inconsistency.
  const strategy: DataSourceStrategy<SessionTranscript[]> = {
    readDemo: () => {
      const demoMetas = getDemoSessions();
      return demoMetas.map((m: SessionMeta) => ({
        ...m,
        task: `Demo Task for ${m.sessionId}`,
        model: "sakthai-v2",
        messages: [
          { role: "user", content: `Execute task in session ${m.sessionId}` },
          { role: "assistant", content: `Task completed successfully.` },
        ],
        result: { text: "Task completed", iterations: 1, stop_reason: "end_turn" },
      }));
    },

    readLive: async () => {
      if (!fs.existsSync(SESSIONS_DIR)) {
        throw new SourceUnavailableError();
      }

      try {
        const files = fs.readdirSync(SESSIONS_DIR).filter((f) => f.endsWith(".json"));
        const loaded: SessionTranscript[] = [];
        for (let idx = 0; idx < files.length; idx++) {
          const file = files[idx];
          try {
            const content = fs.readFileSync(path.join(SESSIONS_DIR, file), "utf8");
            const json = JSON.parse(content);
            const sessionId = json.sessionId || file.replace(".json", "");
            // Same rule as the eval aggregation: only an explicit persona field
            // attributes a session. A transcript without one is labelled
            // "Unattributed" rather than assigned to a persona by file order.
            const slug = resolvePersonaSlug(json);
            const persona = slug ? personaName(slug) : "Unattributed";

            const inputTok = json.usage?.input_tokens || 0;
            const outputTok = json.usage?.output_tokens || 0;
            const tokenUsage = json.usage?.total_tokens || inputTok + outputTok;

            const rawTs = json.timestamp;
            const timestamp =
              typeof rawTs === "number"
                ? new Date(rawTs * 1000).toISOString()
                : typeof rawTs === "string"
                ? rawTs
                : new Date().toISOString();

            const messageCount = Array.isArray(json.messages) ? json.messages.length : 1;
            const status = json.had_error || json.result?.had_error ? "failed" : "completed";

            loaded.push({
              sessionId,
              persona,
              timestamp,
              messageCount,
              tokenUsage,
              status,
              task: json.task || json.task_preview || "",
              model: json.model || "sakthai-v2",
              messages: Array.isArray(json.messages) ? (json.messages as SessionMessage[]) : [],
              result: json.result || {},
            });
          } catch {
            // Safe skip on corrupt file
          }
        }

        return loaded;
      } catch (error) {
        if (error instanceof SourceUnavailableError) throw error;
        throw new SourceReadError(error instanceof Error ? error.message : String(error));
      }
    },
  };

  const { data: allSessions, dataSource } = await resolveDataSource(strategy, !!options?.demo);

  // Handle target single-session detail fetching
  let detail: SessionTranscript | undefined = undefined;
  if (targetId) {
    detail = allSessions.find((s) => s.sessionId === targetId || s.sessionId.includes(targetId));
  }

  // Handle search filtering
  let filtered = allSessions;
  if (search.length > 0) {
    filtered = allSessions.filter((s) => {
      const inId = s.sessionId.toLowerCase().includes(search);
      const inPersona = s.persona.toLowerCase().includes(search);
      const inTask = (s.task || "").toLowerCase().includes(search);
      const inMsg = (s.messages || []).some((m) =>
        (m.content || "").toLowerCase().includes(search)
      );
      return inId || inPersona || inTask || inMsg;
    });
  }

  const total = filtered.length;

  if (offset >= total) {
    return {
      sessions: [],
      total,
      detail,
      dataSource,
    };
  }

  const page = filtered.slice(offset, offset + limit).map((s) => ({
    sessionId: s.sessionId,
    persona: s.persona,
    timestamp: s.timestamp,
    messageCount: s.messageCount,
    tokenUsage: s.tokenUsage,
    status: s.status,
  }));

  return {
    sessions: page,
    total,
    detail,
    dataSource,
  };
}
