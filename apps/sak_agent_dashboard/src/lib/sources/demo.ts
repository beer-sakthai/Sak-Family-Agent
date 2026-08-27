/** Sample data, used when explicitly asked for or when no runtime exists. */

import type {
  AuditPayload,
  MemoryPayload,
  MetricsPayload,
  PersonasPayload,
  SessionsPayload,
  WorkflowRunDetail,
  WorkflowsPayload,
} from "../contracts.generated";
import {
  demoAudit,
  demoMemory,
  demoMetrics,
  demoPersonas,
  demoSessions,
  demoWorkflows,
} from "../demo";
import type { AuditQuery, DashboardSource, MemoryQuery, SessionQuery } from "../source";

export class DemoSource implements DashboardSource {
  readonly kind = "demo" as const;

  async getPersonas(): Promise<PersonasPayload> {
    return demoPersonas();
  }

  async getMetrics(): Promise<MetricsPayload> {
    return demoMetrics();
  }

  async getSessions(query?: SessionQuery): Promise<SessionsPayload> {
    return demoSessions(query);
  }

  async getMemory(query?: MemoryQuery): Promise<MemoryPayload> {
    return demoMemory(query);
  }

  async getAudit(query?: AuditQuery): Promise<AuditPayload> {
    return demoAudit(query);
  }

  async getWorkflows(limit?: number): Promise<WorkflowsPayload> {
    return demoWorkflows(limit);
  }

  async getWorkflow(runId: string): Promise<WorkflowRunDetail | null> {
    const summary = demoWorkflows().runs.find((run) => run.run_id === runId);
    if (!summary) return null;
    return {
      summary,
      steps: Array.from({ length: summary.step_count }, (_, i) => ({
        step_id: `step-${i + 1}`,
        status: i === summary.step_count - 1 && summary.failed_steps > 0 ? "failed" : "completed",
        attempts: 1,
        error: i === summary.step_count - 1 && summary.failed_steps > 0 ? "demo failure" : null,
        started_at: summary.started_at,
        finished_at: summary.finished_at,
        duration_seconds: 12,
      })),
    };
  }
}
