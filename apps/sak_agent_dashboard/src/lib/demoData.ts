/**
 * Demo/sample data — the single definition, shared by the server-side parsers
 * and the client shell.
 *
 * This module must stay free of `fs`/`path`/`os` imports so `page.tsx` (a
 * client component) can import it without pulling Node built-ins into the
 * browser bundle. That constraint is why `lib/sakthai.ts` and `lib/db.ts`
 * re-export from here rather than the other way around.
 *
 * Previously the same figures existed twice — once here-ish in `lib/sakthai.ts`
 * and again as `defaultPersonas`/`defaultMetrics`/... literals inside
 * `page.tsx` — and the two had already drifted (benchmark 96.5 vs 0.96, model
 * `sakthai-v2-qlora` vs `sakthai-v2`, 5 trend points vs 6). One definition
 * removes that class of bug.
 */

import {
  AgentPersona,
  AuditLog,
  MemoryData,
  MetricsData,
  SessionMeta,
} from "./types";
import { PERSONAS } from "./personas";

/** Demo figures, one entry per persona, indexed by roster position. */
export const DEMO_RUNS = [300, 150, 120, 91, 100, 64];
export const DEMO_LATENCIES = [320, 540, 410, 290, 380, 260];
export const DEMO_BENCHMARKS = [96.5, 94.0, 91.0, 98.0, 92.0, 89.5];

/** Derived so it cannot drift from the per-persona demo run counts. */
export const DEMO_TOTAL_RUNS = DEMO_RUNS.reduce((a, b) => a + b, 0);

export function getDemoAgents(): AgentPersona[] {
  return PERSONAS.map((p, idx) => ({
    slug: p.slug,
    name: p.name,
    role: p.role,
    status: idx === 0 ? "Active" : "Ready",
    model: p.model,
    provider: p.provider,
    skills: [...p.skills],
    badge: p.badge,
    benchmarkScore: DEMO_BENCHMARKS[idx],
    runs: DEMO_RUNS[idx],
    latencyMs: DEMO_LATENCIES[idx],
  }));
}

export function getDemoMetrics(): MetricsData {
  const maxTokens = 21;
  return {
    totalRuns: DEMO_TOTAL_RUNS,
    avgLatencyMs: 388,
    successRate: 0.985,
    tokenStats: {
      totalTokens: 1450000,
      promptTokens: 950000,
      completionTokens: 500000,
    },
    stopReasons: {
      end_turn: DEMO_TOTAL_RUNS - maxTokens,
      max_tokens: maxTokens,
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
  const personas = PERSONAS.map((p) => p.name);
  const sessions: SessionMeta[] = [];
  const lastIdx = personas.length - 1;

  let pIdx = 0;
  let pCount = 0;
  for (let i = 1; i <= DEMO_TOTAL_RUNS; i++) {
    if (pCount >= DEMO_RUNS[pIdx] && pIdx < lastIdx) {
      pIdx++;
      pCount = 0;
    }
    pCount++;
    const padded = String(i).padStart(3, "0");
    sessions.push({
      sessionId: `sess-${padded}`,
      persona: personas[pIdx],
      timestamp: "2026-08-02T10:00:00Z",
      messageCount: 12,
      tokenUsage: 4500,
      status: i % 50 === 0 ? "failed" : "completed",
    });
  }
  return sessions;
}

export function getDemoMemoryData(): MemoryData {
  return {
    facts: [
      {
        id: 1,
        entity: "SakThai",
        fact: "Primary model initialized with v2 architecture",
        persona: "SakThai",
        createdAt: "2026-08-02T12:00:00Z",
      },
      {
        id: 2,
        entity: "SakKing",
        fact: "Math proof solver loaded and verified",
        persona: "SakKing",
        createdAt: "2026-08-02T11:45:00Z",
      },
      {
        id: 3,
        entity: "SakSee",
        fact: "Vision image parser cached and operational",
        persona: "SakSee",
        createdAt: "2026-08-02T11:30:00Z",
      },
      {
        id: 4,
        entity: "SakSit",
        fact: "Security boundary rules enforced for filesystem access",
        persona: "SakSit",
        createdAt: "2026-08-02T11:00:00Z",
      },
      {
        id: 5,
        entity: "SakJules",
        fact: "Async background worker queue initialized",
        persona: "SakJules",
        createdAt: "2026-08-02T10:30:00Z",
      },
      {
        id: 6,
        entity: "SakTan",
        fact: "Daily ops rhythm and cron schedule loaded",
        persona: "SakTan",
        createdAt: "2026-08-02T10:00:00Z",
      },
    ],
    observations: [
      {
        id: 1,
        category: "eval",
        observation: "Benchmark 95% passed across test suites",
        timestamp: "2026-08-02T12:00:00Z",
      },
      {
        id: 2,
        category: "telemetry",
        observation: "Average latency stable at 388ms",
        timestamp: "2026-08-02T11:50:00Z",
      },
      {
        id: 3,
        category: "security",
        observation: "Zero unauthorized memory access attempts detected",
        timestamp: "2026-08-02T11:15:00Z",
      },
    ],
  };
}
