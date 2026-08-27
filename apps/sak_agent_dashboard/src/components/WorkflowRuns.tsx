"use client";

import React, { useState } from "react";
import { CheckCircle2, CircleDashed, GitBranch, Loader2, X, XCircle } from "lucide-react";

import type { WorkflowRunDetail, WorkflowRunSummary } from "@/lib/contracts.generated";

interface WorkflowRunsProps {
  runs: WorkflowRunSummary[];
  onRunSelect: (runId: string | null) => void;
  detail: WorkflowRunDetail | null;
  isLoadingDetail?: boolean;
}

/** Statuses arrive lowercased from both sources — see the contract. */
const STATUS_STYLES: Record<string, { classes: string; icon: React.ReactNode }> = {
  completed: {
    classes: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  failed: {
    classes: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    icon: <XCircle className="h-3 w-3" />,
  },
  running: {
    classes: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  pending: {
    classes: "bg-slate-800/80 text-slate-400 border-slate-700",
    icon: <CircleDashed className="h-3 w-3" />,
  },
  skipped: {
    classes: "bg-slate-900/80 text-slate-500 border-slate-800",
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
  detail,
  isLoadingDetail = false,
}: WorkflowRunsProps) {
  const [openRunId, setOpenRunId] = useState<string | null>(null);

  const open = (runId: string) => {
    setOpenRunId(runId);
    onRunSelect(runId);
  };
  const close = () => {
    setOpenRunId(null);
    onRunSelect(null);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-violet-400" />
            Workflow Runs
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            DAG executions from{" "}
            <code className="text-slate-300">~/.sakthai/workflow_runs/</code>
          </p>
        </div>
        <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-violet-400">
          {runs.length} {runs.length === 1 ? "run" : "runs"}
        </span>
      </div>

      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3">Workflow</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Started</th>
                <th className="px-5 py-3 text-right">Duration</th>
                <th className="px-5 py-3 text-right">Steps</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-slate-500 italic">
                    No workflow runs recorded yet.
                  </td>
                </tr>
              ) : (
                runs.map((run) => (
                  <tr key={run.run_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-3.5">
                      <span className="font-bold text-slate-100">{run.workflow_name || "—"}</span>
                      <span className="block text-[10px] text-slate-500">{run.run_id}</span>
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusPill status={run.status} />
                    </td>
                    <td className="px-5 py-3.5 text-slate-500 text-[11px] whitespace-nowrap">
                      {started(run.started_at)}
                    </td>
                    <td className="px-5 py-3.5 text-right text-slate-300">
                      {duration(run.duration_seconds)}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <span className="text-slate-300">{run.step_count}</span>
                      {run.failed_steps > 0 && (
                        <span className="text-rose-400"> ({run.failed_steps} failed)</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => open(run.run_id)}
                        className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-violet-300 hover:border-violet-600/60 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
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
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Workflow run steps"
          onClick={close}
        >
          <div
            className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 flex items-center justify-between px-6 py-4 bg-slate-900 border-b border-slate-800">
              <h4 className="font-display font-bold text-white flex items-center gap-2">
                <GitBranch className="h-4 w-4 text-violet-400" />
                {detail?.summary.workflow_name ?? openRunId}
              </h4>
              <button
                onClick={close}
                aria-label="Close run detail"
                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="p-6 space-y-3 font-mono text-xs">
              {isLoadingDetail ? (
                <p className="text-slate-500 italic">Loading steps…</p>
              ) : !detail ? (
                <p className="text-slate-500 italic">This run could not be loaded.</p>
              ) : detail.steps.length === 0 ? (
                <p className="text-slate-500 italic">This run recorded no steps.</p>
              ) : (
                detail.steps.map((step) => (
                  <div
                    key={step.step_id}
                    className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-bold text-slate-100">{step.step_id || "—"}</span>
                      <StatusPill status={step.status} />
                    </div>
                    <div className="flex items-center gap-4 text-[11px] text-slate-500">
                      <span>{duration(step.duration_seconds)}</span>
                      <span>
                        {step.attempts} {step.attempts === 1 ? "attempt" : "attempts"}
                      </span>
                    </div>
                    {step.error && (
                      <p className="text-rose-300 font-sans break-words">{step.error}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default WorkflowRuns;
