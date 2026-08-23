/**
 * Self-Healing Recovery Engine for sak_agent_dashboard.
 * Coordinates DLQ inspection, persona circuit status, and incident telemetry.
 */

import { TelemetryEvent } from "./types";
import { telemetryBus } from "./telemetryBus";

export interface IncidentRecord {
  id: string;
  persona: string;
  action: string;
  severity: "transient" | "state_corrupt" | "fatal";
  errorType: string;
  errorMessage: string;
  retryCount: number;
  maxRetries: number;
  status: "pending" | "replayed" | "quarantined";
  createdAt: string;
  updatedAt: string;
}

export interface PersonaHealthSummary {
  persona: string;
  status: "healthy" | "degraded" | "quarantined";
  circuitBreaker: "CLOSED" | "OPEN" | "HALF-OPEN";
  failureCount: number;
  pendingDlqCount: number;
  lastIncidentAt?: string;
}

class SelfHealingDashboardEngine {
  private incidents: IncidentRecord[] = [
    {
      id: "dlq_sim_01",
      persona: "SakSee",
      action: "Scout HuggingFace Hub Spaces",
      severity: "transient",
      errorType: "HTTPError429",
      errorMessage: "Rate limit exceeded (429 Too Many Requests)",
      retryCount: 1,
      maxRetries: 3,
      status: "pending",
      createdAt: new Date(Date.now() - 120_000).toISOString(),
      updatedAt: new Date(Date.now() - 60_000).toISOString(),
    },
    {
      id: "dlq_sim_02",
      persona: "SakKing",
      action: "AST Guardrail Verification",
      severity: "state_corrupt",
      errorType: "OperationalError",
      errorMessage: "SQLite database busy / savepoint lock contention",
      retryCount: 0,
      maxRetries: 3,
      status: "pending",
      createdAt: new Date(Date.now() - 300_000).toISOString(),
      updatedAt: new Date(Date.now() - 300_000).toISOString(),
    },
  ];

  getIncidents(): IncidentRecord[] {
    return this.incidents;
  }

  getPersonaHealth(): PersonaHealthSummary[] {
    const personas = ["SakThai", "SakKing", "SakSee", "SakSit", "SakJules", "SakTan"];
    return personas.map((p) => {
      const pending = this.incidents.filter((i) => i.persona.toLowerCase() === p.toLowerCase() && i.status === "pending");
      const hasCorrupt = pending.some((i) => i.severity === "state_corrupt" || i.severity === "fatal");
      
      let status: "healthy" | "degraded" | "quarantined" = "healthy";
      let circuit: "CLOSED" | "OPEN" | "HALF-OPEN" = "CLOSED";

      if (pending.length > 0) {
        status = hasCorrupt ? "quarantined" : "degraded";
        circuit = hasCorrupt ? "OPEN" : "HALF-OPEN";
      }

      return {
        persona: p,
        status,
        circuitBreaker: circuit,
        failureCount: pending.length,
        pendingDlqCount: pending.length,
        lastIncidentAt: pending[0]?.updatedAt,
      };
    });
  }

  replayIncident(id: string): { success: boolean; incident?: IncidentRecord } {
    const idx = this.incidents.findIndex((i) => i.id === id);
    if (idx === -1) return { success: false };

    this.incidents[idx].status = "replayed";
    this.incidents[idx].updatedAt = new Date().toISOString();

    telemetryBus.emitEvent({
      type: "agent_complete",
      persona: this.incidents[idx].persona,
      data: {
        message: `Self-healing replay successful for task: ${this.incidents[idx].action}`,
      },
    });

    return { success: true, incident: this.incidents[idx] };
  }

  resetCircuit(persona: string): boolean {
    this.incidents = this.incidents.map((i) =>
      i.persona.toLowerCase() === persona.toLowerCase() && i.status === "pending"
        ? { ...i, status: "replayed", updatedAt: new Date().toISOString() }
        : i
    );
    return true;
  }
}

export const selfHealingDashboardEngine = new SelfHealingDashboardEngine();
