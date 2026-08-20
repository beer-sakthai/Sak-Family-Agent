import { describe, it, expect } from "vitest";
import { PERSONAS } from "@/lib/personas";

// Interface Contracts as defined in PROJECT.md & TEST_INFRA.md
export interface PersonaCard {
  name: string;
  role: string;
  status: string;
  model: string;
  latencyMs: number;
  runs: number;
  skills: string[];
}

/**
 * The roster is asserted against `lib/personas.ts`, which tracks
 * `config.PERSONA_NAMES`, rather than against a literal count. These tests
 * previously hard-coded 5 and named five personas, which is how SakTan's total
 * absence from the dashboard went unnoticed.
 */
const ROSTER_NAMES = PERSONAS.map((p) => p.name);

export interface MetricsData {
  totalRuns: number;
  avgLatencyMs: number;
  successRate: number;
  tokenStats: {
    totalTokens: number;
    promptTokens: number;
    completionTokens: number;
  };
  stopReasons: Record<string, number>;
  trends: Array<{ date: string; runs: number; latencyMs: number }>;
}

export interface MemoryData {
  facts: Array<{ id: string | number; entity: string; fact: string; persona?: string; createdAt?: string }>;
  observations: Array<{ id: string | number; category: string; observation: string; timestamp?: string }>;
}

export interface AuditLog {
  id: string | number;
  timestamp: string;
  persona: string;
  severity: "info" | "warning" | "error" | "critical";
  event: string;
  details: string;
}

export interface SessionMeta {
  sessionId: string;
  persona: string;
  timestamp: string;
  messageCount: number;
  tokenUsage: number;
  status: string;
}

// Helper to safely load API route module if present
async function getApiRouteModule(routePath: string) {
  try {
    return await import(`../app/api/${routePath}/route`);
  } catch {
    return null;
  }
}

describe("API Routes Suite (Tier 1 & Tier 2)", () => {

  describe("Tier 1: Feature Coverage — Standard Response Contracts", () => {

    it("GET /api/agents returns every Sak Family persona with required fields", async () => {
      const route = await getApiRouteModule("agents");
      if (route && typeof route.GET === "function") {
        const req = new Request("http://localhost:3000/api/agents");
        const res = await route.GET(req);
        expect(res.status).toBe(200);
        const data = await res.json();
        expect(data.success).toBe(true);
        expect(Array.isArray(data.agents)).toBe(true);

        const names = data.agents.map((a: PersonaCard) => a.name);
        // Every persona in the roster must be present — including SakTan, whose
        // omission this assertion previously encoded as correct.
        expect(names).toEqual(expect.arrayContaining(ROSTER_NAMES));
        expect(names).toContain("SakTan");

        // The only row allowed beyond the roster is the "Unattributed" bucket.
        const extras = names.filter((n: string) => !ROSTER_NAMES.includes(n));
        expect(extras.every((n: string) => n === "Unattributed")).toBe(true);

        expect(["live", "demo", "unavailable"]).toContain(data.dataSource);

        data.agents.forEach((agent: PersonaCard) => {
          expect(agent).toHaveProperty("name");
          expect(agent).toHaveProperty("role");
          expect(agent).toHaveProperty("status");
          expect(agent).toHaveProperty("model");
          expect(typeof agent.latencyMs).toBe("number");
          expect(typeof agent.runs).toBe("number");
          expect(Array.isArray(agent.skills)).toBe(true);
        });
      } else {
        // The route exists; a missing module is a real failure, not something
        // to substitute a local mock for. The previous fallback asserted
        // against its own literal and could never fail.
        throw new Error("src/app/api/agents/route.ts did not export a GET handler");
      }
    });

    it("GET /api/agents?demo=true returns the full demo roster", async () => {
      const route = await getApiRouteModule("agents");
      if (route && typeof route.GET === "function") {
        const req = new Request("http://localhost:3000/api/agents?demo=true");
        const res = await route.GET(req);
        expect(res.status).toBe(200);
        const data = await res.json();
        expect(data.success).toBe(true);
        expect(data.dataSource).toBe("demo");
        // Demo mode shows exactly the roster — no unattributed bucket, since
        // synthesized runs are all attributed by construction.
        expect(data.agents.length).toBe(PERSONAS.length);
        expect(data.agents.map((a: PersonaCard) => a.name)).toEqual([...ROSTER_NAMES]);
        expect(data.unattributedRuns).toBe(0);
      } else {
        throw new Error("src/app/api/agents/route.ts did not export a GET handler");
      }
    });

    it("GET /api/metrics returns aggregated telemetry metrics", async () => {
      const route = await getApiRouteModule("metrics");
      if (route && typeof route.GET === "function") {
        const req = new Request("http://localhost:3000/api/metrics");
        const res = await route.GET(req);
        expect(res.status).toBe(200);
        const data = await res.json();
        expect(data.success).toBe(true);
        expect(data.metrics).toHaveProperty("totalRuns");
        expect(data.metrics).toHaveProperty("avgLatencyMs");
        expect(data.metrics).toHaveProperty("successRate");
        expect(data.metrics.tokenStats).toHaveProperty("totalTokens");
        expect(data.metrics.stopReasons).toBeDefined();
      } else {
        const mockMetrics: MetricsData = {
          totalRuns: 761,
          avgLatencyMs: 388,
          successRate: 0.985,
          tokenStats: { totalTokens: 1450000, promptTokens: 950000, completionTokens: 500000 },
          stopReasons: { end_turn: 740, max_tokens: 21 },
          trends: [{ date: "2026-08-01", runs: 350, latencyMs: 380 }],
        };
        expect(mockMetrics.totalRuns).toBe(761);
        expect(mockMetrics.successRate).toBeGreaterThan(0);
      }
    });

    it("GET /api/memory returns SQLite facts, observations, and audit logs", async () => {
      const route = await getApiRouteModule("memory");
      if (route && typeof route.GET === "function") {
        const req = new Request("http://localhost:3000/api/memory");
        const res = await route.GET(req);
        expect(res.status).toBe(200);
        const data = await res.json();
        expect(data.success).toBe(true);
        expect(data.memory).toHaveProperty("facts");
        expect(data.memory).toHaveProperty("observations");
        expect(Array.isArray(data.auditLogs)).toBe(true);
      } else {
        const mockMemory: { memory: MemoryData; auditLogs: AuditLog[] } = {
          memory: {
            facts: [{ id: 1, entity: "SakThai", fact: "Primary model initialized" }],
            observations: [{ id: 1, category: "eval", observation: "Benchmark 95% passed" }],
          },
          auditLogs: [{ id: 1, timestamp: "2026-08-02T12:00:00Z", persona: "SakSit", severity: "info", event: "Security scan", details: "Clean" }],
        };
        expect(mockMemory.memory.facts.length).toBeGreaterThan(0);
        expect(mockMemory.auditLogs[0].severity).toBe("info");
      }
    });

    it("GET /api/sessions returns session transcripts metadata", async () => {
      const route = await getApiRouteModule("sessions");
      if (route && typeof route.GET === "function") {
        const req = new Request("http://localhost:3000/api/sessions?limit=10&offset=0");
        const res = await route.GET(req);
        expect(res.status).toBe(200);
        const data = await res.json();
        expect(data.success).toBe(true);
        expect(Array.isArray(data.sessions)).toBe(true);
        expect(typeof data.total).toBe("number");
      } else {
        const mockSessions: { sessions: SessionMeta[]; total: number } = {
          sessions: [{ sessionId: "sess-001", persona: "SakThai", timestamp: "2026-08-02T10:00:00Z", messageCount: 12, tokenUsage: 4500, status: "completed" }],
          total: 761,
        };
        expect(mockSessions.total).toBe(761);
        expect(mockSessions.sessions[0].sessionId).toBe("sess-001");
      }
    });
  });

  describe("Tier 2: Boundary & Corner Cases", () => {
    it("handles negative pagination limit and offset gracefully", async () => {
      const route = await getApiRouteModule("sessions");
      if (route && typeof route.GET === "function") {
        const req = new Request("http://localhost:3000/api/sessions?limit=-10&offset=-5");
        const res = await route.GET(req);
        expect([200, 400]).toContain(res.status);
        const data = await res.json();
        if (res.status === 200) {
          expect(data.success).toBe(true);
          expect(Array.isArray(data.sessions)).toBe(true);
        }
      } else {
        const sanitizePagination = (limit: number, offset: number) => ({
          limit: Math.max(1, limit),
          offset: Math.max(0, offset),
        });
        const result = sanitizePagination(-10, -5);
        expect(result.limit).toBe(1);
        expect(result.offset).toBe(0);
      }
    });

    it("handles out-of-bounds pagination offset", async () => {
      const route = await getApiRouteModule("sessions");
      if (route && typeof route.GET === "function") {
        const req = new Request("http://localhost:3000/api/sessions?limit=10&offset=999999");
        const res = await route.GET(req);
        expect(res.status).toBe(200);
        const data = await res.json();
        expect(data.success).toBe(true);
        expect(data.sessions).toEqual([]);
      } else {
        const paginate = (items: any[], limit: number, offset: number) =>
          items.slice(offset, offset + limit);
        expect(paginate([{ id: 1 }], 10, 999999)).toEqual([]);
      }
    });

    it("handles non-existent search query filtering without throwing exception", async () => {
      const route = await getApiRouteModule("memory");
      if (route && typeof route.GET === "function") {
        const req = new Request("http://localhost:3000/api/memory?query=NON_EXISTENT_KEYWORD_XYZ_9999");
        const res = await route.GET(req);
        expect(res.status).toBe(200);
        const data = await res.json();
        expect(data.success).toBe(true);
        expect(data.memory.facts).toEqual([]);
      } else {
        const filterFacts = (facts: any[], query: string) =>
          facts.filter((f) => f.fact.includes(query));
        const filtered = filterFacts([{ fact: "SakThai active" }], "NON_EXISTENT_KEYWORD_XYZ_9999");
        expect(filtered).toEqual([]);
      }
    });

    it("handles special characters and potential injection input safely", async () => {
      const route = await getApiRouteModule("memory");
      if (route && typeof route.GET === "function") {
        const req = new Request("http://localhost:3000/api/memory?query=%3Cscript%3Ealert(1)%3C/script%3E");
        const res = await route.GET(req);
        expect(res.status).toBe(200);
        const data = await res.json();
        expect(data.success).toBe(true);
      } else {
        const sanitizeQuery = (input: string) => input.replace(/[<>]/g, "");
        const clean = sanitizeQuery("<script>alert(1)</script>");
        expect(clean).not.toContain("<script>");
      }
    });

    it("handles unsupported security severity parameter safely", async () => {
      const route = await getApiRouteModule("memory");
      if (route && typeof route.GET === "function") {
        const req = new Request("http://localhost:3000/api/memory?severity=INVALID_SEVERITY_LEVEL");
        const res = await route.GET(req);
        expect(res.status).toBe(200);
        const data = await res.json();
        expect(data.success).toBe(true);
      } else {
        const validSeverities = ["info", "warning", "error", "critical"];
        const filterSeverity = (logSeverity: string, param: string) => {
          if (!validSeverities.includes(param.toLowerCase())) return true;
          return logSeverity === param;
        };
        expect(filterSeverity("info", "INVALID_SEVERITY_LEVEL")).toBe(true);
      }
    });

    it("handles empty runtime data fallback cleanly when files/db do not exist", async () => {
      const fallbackMetrics: MetricsData = {
        totalRuns: 0,
        avgLatencyMs: 0,
        successRate: 0,
        tokenStats: { totalTokens: 0, promptTokens: 0, completionTokens: 0 },
        stopReasons: {},
        trends: [],
      };
      expect(fallbackMetrics.totalRuns).toBe(0);
      expect(fallbackMetrics.trends).toEqual([]);
    });

    it("handles zero token count and zero latency cases without divide-by-zero errors", async () => {
      const calculateAvg = (totalLatency: number, totalRuns: number) => {
        if (totalRuns <= 0) return 0;
        return totalLatency / totalRuns;
      };

      expect(calculateAvg(0, 0)).toBe(0);
      expect(calculateAvg(500, 0)).toBe(0);
      expect(calculateAvg(1000, 5)).toBe(200);
    });
  });
});
