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
} from "./types";

const SAKTHAI_DIR = process.env.SAKTHAI_DIR || path.join(os.homedir(), ".sakthai");
const EVAL_FILE = path.join(SAKTHAI_DIR, "eval.jsonl");
const AUDIT_FILE = path.join(SAKTHAI_DIR, "audit.log");
const SESSIONS_DIR = path.join(SAKTHAI_DIR, "sessions");

const DEFAULT_PERSONAS: Array<Omit<AgentPersona, "runs" | "latencyMs">> = [
  {
    name: "SakThai",
    role: "Primary Orchestrator",
    status: "Active",
    model: "sakthai-v2",
    skills: ["routing", "planning", "evaluation"],
    badge: "Primary",
    benchmarkScore: 0.96,
  },
  {
    name: "SakKing",
    role: "Reasoning Specialist",
    status: "Ready",
    model: "sakking-v1",
    skills: ["reasoning", "math-proof", "logic"],
    badge: "Reasoning",
    benchmarkScore: 0.94,
  },
  {
    name: "SakSee",
    role: "Multimodal Specialist",
    status: "Ready",
    model: "saksee-v1",
    skills: ["vision", "multimodal", "ocr"],
    badge: "Vision",
    benchmarkScore: 0.91,
  },
  {
    name: "SakSit",
    role: "Security Auditor",
    status: "Ready",
    model: "saksit-v1",
    skills: ["audit", "vulnerability-scan", "sandbox"],
    badge: "Security",
    benchmarkScore: 0.98,
  },
  {
    name: "SakJules",
    role: "Async Specialist",
    status: "Ready",
    model: "sakjules-v1",
    skills: ["async-tasks", "cron-execution", "background"],
    badge: "Async",
    benchmarkScore: 0.92,
  },
];

function getPersonaIndexForRun(entry: any, index: number): number {
  if (entry.persona) {
    const pName = String(entry.persona).toLowerCase();
    if (pName.includes("thai")) return 0;
    if (pName.includes("king")) return 1;
    if (pName.includes("see")) return 2;
    if (pName.includes("sit")) return 3;
    if (pName.includes("jules")) return 4;
  }
  if (entry.model) {
    const mName = String(entry.model).toLowerCase();
    if (mName.includes("claude") || mName.includes("sakthai")) return 0;
    if (mName.includes("gpt") || mName.includes("sakking")) return 1;
    if (mName.includes("gemini") || mName.includes("saksee")) return 2;
    if (mName.includes("llama") || mName.includes("saksit")) return 3;
    if (mName.includes("qwen") || mName.includes("sakjules")) return 4;
  }
  return index % 5;
}

export function getDemoAgents(): AgentPersona[] {
  const demoRuns = [300, 150, 120, 91, 100];
  const demoLatencies = [320, 540, 410, 290, 380];
  return DEFAULT_PERSONAS.map((p, idx) => ({
    ...p,
    runs: demoRuns[idx],
    latencyMs: demoLatencies[idx],
  }));
}

export function getDemoMetrics(): MetricsData {
  return {
    totalRuns: 761,
    avgLatencyMs: 388,
    successRate: 0.985,
    tokenStats: {
      totalTokens: 1450000,
      promptTokens: 950000,
      completionTokens: 500000,
    },
    stopReasons: {
      end_turn: 740,
      max_tokens: 21,
    },
    trends: [
      { date: "2026-07-27", runs: 95, latencyMs: 375 },
      { date: "2026-07-28", runs: 110, latencyMs: 390 },
      { date: "2026-07-29", runs: 125, latencyMs: 380 },
      { date: "2026-07-30", runs: 140, latencyMs: 400 },
      { date: "2026-07-31", runs: 130, latencyMs: 385 },
      { date: "2026-08-01", runs: 161, latencyMs: 388 },
    ],
  };
}

export function getDemoAuditLogs(): AuditLog[] {
  return [
    {
      id: 1,
      timestamp: "2026-08-02T12:00:00Z",
      persona: "SakSit",
      severity: "info",
      event: "Security scan completed",
      details: "Memory and process execution boundaries verified.",
    },
    {
      id: 2,
      timestamp: "2026-08-02T11:30:00Z",
      persona: "SakSit",
      severity: "warning",
      event: "Unusual token consumption",
      details: "Session sess-042 exceeded token budget threshold.",
    },
    {
      id: 3,
      timestamp: "2026-08-02T10:15:00Z",
      persona: "SakSit",
      severity: "critical",
      event: "Symlink boundary check",
      details: "Prevented access outside sandbox.",
    },
    {
      id: 4,
      timestamp: "2026-08-02T09:00:00Z",
      persona: "SakThai",
      severity: "info",
      event: "Session dispatch",
      details: "Orchestrated task execution across subagents.",
    },
  ];
}

export function getDemoSessions(): SessionMeta[] {
  const personas = ["SakThai", "SakKing", "SakSee", "SakSit", "SakJules"];
  const sessions: SessionMeta[] = [];
  const total = 761;
  const demoDistribution = [300, 150, 120, 91, 100];

  let pIdx = 0;
  let pCount = 0;
  for (let i = 1; i <= total; i++) {
    if (pCount >= demoDistribution[pIdx] && pIdx < 4) {
      pIdx++;
      pCount = 0;
    }
    pCount++;
    const persona = personas[pIdx];
    const padded = String(i).padStart(3, "0");
    sessions.push({
      sessionId: `sess-${padded}`,
      persona,
      timestamp: "2026-08-02T10:00:00Z",
      messageCount: 12,
      tokenUsage: 4500,
      status: i % 50 === 0 ? "failed" : "completed",
    });
  }
  return sessions;
}

export async function getAgentOverview(demo?: boolean): Promise<AgentPersona[]> {
  if (demo) {
    return getDemoAgents();
  }

  try {
    if (!fs.existsSync(EVAL_FILE)) {
      return getDemoAgents();
    }

    const fileContent = fs.readFileSync(EVAL_FILE, "utf8");
    const lines = fileContent.split("\n").filter((l) => l.trim().length > 0);

    if (lines.length === 0) {
      return getDemoAgents();
    }

    const personaStats = DEFAULT_PERSONAS.map((p) => ({
      ...p,
      runs: 0,
      totalLatencyMs: 0,
    }));

    lines.forEach((line, index) => {
      try {
        const entry = JSON.parse(line);
        const idx = getPersonaIndexForRun(entry, index);
        personaStats[idx].runs += 1;
        const latencyMs = Math.round((entry.latency_s || entry.latencyMs || 0.3) * 1000);
        personaStats[idx].totalLatencyMs += latencyMs;
      } catch {
        // Safe skip on corrupt line
      }
    });

    return personaStats.map((p) => {
      const avgLatencyMs = p.runs > 0 ? Math.round(p.totalLatencyMs / p.runs) : 0;
      const { totalLatencyMs, ...rest } = p;
      return {
        ...rest,
        latencyMs: avgLatencyMs,
      };
    });
  } catch {
    return getDemoAgents();
  }
}

export async function getMetricsSummary(demo?: boolean): Promise<MetricsData> {
  if (demo) {
    return getDemoMetrics();
  }

  try {
    if (!fs.existsSync(EVAL_FILE)) {
      return getDemoMetrics();
    }

    const fileContent = fs.readFileSync(EVAL_FILE, "utf8");
    const lines = fileContent.split("\n").filter((l) => l.trim().length > 0);

    if (lines.length === 0) {
      return {
        totalRuns: 0,
        avgLatencyMs: 0,
        successRate: 0,
        tokenStats: { totalTokens: 0, promptTokens: 0, completionTokens: 0 },
        stopReasons: {},
        trends: [],
      };
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
      return {
        totalRuns: 0,
        avgLatencyMs: 0,
        successRate: 0,
        tokenStats: { totalTokens: 0, promptTokens: 0, completionTokens: 0 },
        stopReasons: {},
        trends: [],
      };
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
  } catch {
    return getDemoMetrics();
  }
}

export async function getAuditLogs(
  demo?: boolean,
  severityFilter?: string
): Promise<AuditLog[]> {
  const validSeverities: AuditSeverity[] = ["info", "warning", "error", "critical"];

  const parseSeverity = (raw: string): AuditSeverity => {
    const s = String(raw || "").toLowerCase();
    if (s === "high" || s === "critical") return "critical";
    if (s === "medium" || s === "warning") return "warning";
    if (s === "error") return "error";
    return "info";
  };

  let logs: AuditLog[] = [];

  if (demo || !fs.existsSync(AUDIT_FILE)) {
    logs = getDemoAuditLogs();
  } else {
    try {
      const fileContent = fs.readFileSync(AUDIT_FILE, "utf8");
      const lines = fileContent.split("\n").filter((l) => l.trim().length > 0);

      logs = lines.map((line, idx) => {
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
            severity: "info",
            event: "Unparseable Audit Event",
            details: line,
          };
        }
      });
    } catch {
      logs = getDemoAuditLogs();
    }
  }

  if (severityFilter && severityFilter.trim().length > 0) {
    const filterLower = severityFilter.toLowerCase();
    if (validSeverities.includes(filterLower as AuditSeverity)) {
      logs = logs.filter((l) => l.severity === filterLower);
    }
    // Note: If severityFilter is invalid (e.g. "INVALID_SEVERITY_LEVEL"), return all logs unchanged per spec/tests
  }

  return logs;
}

export async function getSessionTranscripts(options?: {
  demo?: boolean;
  search?: string;
  limit?: number;
  offset?: number;
  id?: string;
}): Promise<{ sessions: SessionMeta[]; total: number; detail?: SessionTranscript }> {
  let limit = Math.min(100, Math.max(1, Math.floor(options?.limit ?? 20)));
  let offset = Math.max(0, Math.floor(options?.offset ?? 0));
  const search = options?.search ? options.search.trim().toLowerCase() : "";
  const targetId = options?.id ? options.id.trim() : null;

  let allSessions: SessionTranscript[] = [];

  if (options?.demo || !fs.existsSync(SESSIONS_DIR)) {
    const demoMetas = getDemoSessions();
    allSessions = demoMetas.map((m) => ({
      ...m,
      task: `Demo Task for ${m.sessionId}`,
      model: "sakthai-v2",
      messages: [
        { role: "user", content: `Execute task in session ${m.sessionId}` },
        { role: "assistant", content: `Task completed successfully.` },
      ],
      result: { text: "Task completed", iterations: 1, stop_reason: "end_turn" },
    }));
  } else {
    try {
      const files = fs.readdirSync(SESSIONS_DIR).filter((f) => f.endsWith(".json"));
      const loaded: SessionTranscript[] = [];
      for (let idx = 0; idx < files.length; idx++) {
        const file = files[idx];
        try {
          const content = fs.readFileSync(path.join(SESSIONS_DIR, file), "utf8");
          const json = JSON.parse(content);
          const sessionId = json.sessionId || file.replace(".json", "");
          const personaIndex = getPersonaIndexForRun(json, idx);
          const personaNames = ["SakThai", "SakKing", "SakSee", "SakSit", "SakJules"];
          const persona = json.persona || personaNames[personaIndex];

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

      allSessions = loaded;
    } catch {
      const demoMetas = getDemoSessions();
      allSessions = demoMetas.map((m) => ({ ...m }));
    }
  }

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
  };
}
