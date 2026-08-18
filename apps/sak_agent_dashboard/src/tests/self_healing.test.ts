import { describe, it, expect } from "vitest";
import { selfHealingDashboardEngine } from "@/lib/selfHealingEngine";

describe("Self-Healing Dashboard Engine", () => {
  it("fetches incidents and computes persona health summaries", () => {
    const incidents = selfHealingDashboardEngine.getIncidents();
    expect(incidents.length).toBeGreaterThanOrEqual(2);

    const health = selfHealingDashboardEngine.getPersonaHealth();
    expect(health.length).toBe(6);

    const sakSeeHealth = health.find((h) => h.persona === "SakSee");
    expect(sakSeeHealth).toBeDefined();
    expect(sakSeeHealth?.status).toBe("degraded");
  });

  it("replays incident and updates status", () => {
    const res = selfHealingDashboardEngine.replayIncident("dlq_sim_01");
    expect(res.success).toBe(true);
    expect(res.incident?.status).toBe("replayed");
  });

  it("resets circuit breaker for persona", () => {
    const ok = selfHealingDashboardEngine.resetCircuit("SakKing");
    expect(ok).toBe(true);

    const health = selfHealingDashboardEngine.getPersonaHealth();
    const sakKing = health.find((h) => h.persona === "SakKing");
    expect(sakKing?.status).toBe("healthy");
  });
});
