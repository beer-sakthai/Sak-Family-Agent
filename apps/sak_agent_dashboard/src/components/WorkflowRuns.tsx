"use client";

import React from "react";
import { CheckCircle2, CircleDashed, GitBranch, Info, Loader2, XCircle } from "lucide-react";

import type { WorkflowRunDetail, WorkflowRunSummary } from "@/lib/contracts.generated";
import Drawer from "./Drawer";

interface WorkflowRunsProps {
  runs: WorkflowRunSummary[];
  onRunSelect: (runId: string | null) => void;
  /** The open run's id, owned by the page because it lives in the URL. */
  openRunId: string | null;
  /**
   * True when a persona filter is active. Workflow runs record no persona, so
   * this panel cannot honour it — and says so rather than letting the filter in
   * the topbar imply these rows were narrowed.
   */
  familyWide?: boolean;
  detail: WorkflowRunDetail | null;
  isLoadingDetail?: boolean;
}

/** Statuses arrive lowercased from both sources — see the contract. */
const STATUS_STYLES: Record<string, { classes: string; icon: React.ReactNode }> = {
  completed: {
    classes: "bg-hue-emerald/10 text-hue-emerald border-hue-emerald-line/30",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  failed: {
    classes: "bg-hue-rose/10 text-hue-rose border-hue-rose-line/30",
    icon: <XCircle className="h-3 w-3" />,
  },
  running: {
    classes: "bg-hue-cyan/10 text-hue-cyan border-hue-cyan-line/30",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  pending: {
    classes: "bg-raised/80 text-fg-3 border-line-strong",
    icon: <CircleDashed className="h-3 w-3" />,
  },
  skipped: {
    classes: "bg-panel/80 text-fg-4 border-line",
    icon: <CircleDashed className="h-3 w-3" />,
  },
};

function StatusPill({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.pending;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono border ${style.classes}`}
    >
      {style.icon}
      {status || "unknown"}
    </span>
  );
}

function duration(seconds: number | null): string {
  if (seconds === null) return "—";
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

function started(iso: string | null): string {
  if (!iso) return "—";
  return iso.replace("T", " ").slice(0, 19);
}

export function WorkflowRuns({
  runs,
  onRunSelect,
  openRunId,
  familyWide = false,
  detail,
  isLoadingDetail = false,
}: WorkflowRunsProps) {
  const open = (runId: string) => onRunSelect(runId);
  const close = () => onRunSelect(null);

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-fg tracking-tight flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-hue-violet" />
            Workflow Runs
          </h3>
          <p className="text-xs text-fg-3 mt-0.5">
            DAG executions from{" "}
            <code className="text-fg-2">~/.sakthai/workflow_runs/</code>
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {familyWide && (
            <span
              data-testid="workflows-family-wide"
              title="agent_workflow records no persona, so these runs cannot be attributed to one."
              className="inline-flex items-center gap-1.5 rounded-full border border-hue-amber-line bg-hue-amber-tint/40 px-3 py-1 font-mono text-xs text-hue-amber"
            >
              <Info className="h-3 w-3" aria-hidden />
              Not filtered by persona
            </span>
          )}
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-panel border border-line text-hue-violet">
            {runs.length} {runs.length === 1 ? "run" : "runs"}
          </span>
        </div>
      </div>

      <div className="glass-panel rounded-2xl bg-panel/80 border border-line/80 backdrop-blur-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-sunken/80 text-fg-3 border-b border-line/80 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3">Workflow</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Started</th>
                <th className="px-5 py-3 text-right">Duration</th>
                <th className="px-5 py-3 text-right">Steps</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-line/60 text-fg-2">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-fg-4 italic">
                    No workflow runs recorded yet.
                  </td>
                </tr>
              ) : (
                runs.map((run) => (
                  <tr key={run.run_id} className="hover:bg-raised/40 transition-colors">
                    <td className="px-5 py-3.5">
                      <span className="font-bold text-fg">{run.workflow_name || "—"}</span>
                      <span className="block text-[10px] text-fg-4">{run.run_id}</span>
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusPill status={run.status} />
                    </td>
                    <td className="px-5 py-3.5 text-fg-4 text-[11px] whitespace-nowrap">
                      {started(run.started_at)}
                    </td>
                    <td className="px-5 py-3.5 text-right text-fg-2">
                      {duration(run.duration_seconds)}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <span className="text-fg-2">{run.step_count}</span>
                      {run.failed_steps > 0 && (
                        <span className="text-hue-rose"> ({run.failed_steps} failed)</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => open(run.run_id)}
                        className="text-[11px] px-2.5 py-1 rounded-lg bg-raised border border-line-strong text-hue-violet hover:border-hue-violet-line/60 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-hue-violet"
                      >
                        Steps
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {openRunId && (
        <Drawer
          title={detail?.summary.workflow_name ?? openRunId}
          subtitle={openRunId}
          icon={<GitBranch className="h-4 w-4 text-hue-violet" />}
          onClose={close}
          data-testid="workflow-drawer"
        >
          <div className="space-y-3 font-mono text-xs">
              {isLoadingDetail ? (
                <p className="text-fg-4 italic">Loading steps…</p>
              ) : !detail ? (
                <p className="text-fg-4 italic">This run could not be loaded.</p>
              ) : detail.steps.length === 0 ? (
                <p className="text-fg-4 italic">This run recorded no steps.</p>
              ) : (
                detail.steps.map((step) => (
                  <div
                    key={step.step_id}
                    className="p-3 rounded-xl bg-sunken/60 border border-line space-y-1.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-bold text-fg">{step.step_id || "—"}</span>
                      <StatusPill status={step.status} />
                    </div>
                    <div className="flex items-center gap-4 text-[11px] text-fg-4">
                      <span>{duration(step.duration_seconds)}</span>
                      <span>
                        {step.attempts} {step.attempts === 1 ? "attempt" : "attempts"}
                      </span>
                    </div>
                    {step.error && (
                      <p className="text-hue-rose font-sans break-words">{step.error}</p>
                    )}
                  </div>
                ))
            )}
          </div>
        </Drawer>
      )}
    </div>
  );
}

export default WorkflowRuns;
