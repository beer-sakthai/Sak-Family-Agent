'use client';

import React, { useState } from 'react';

interface ToolExecutionCardProps {
  persona: string;
  tool: string;
  args: Record<string, unknown>;
  output?: string;
  astSafe?: boolean;
  requiresApproval?: boolean;
  onApprove?: () => void;
  onReject?: () => void;
}

export const ToolExecutionCard: React.FC<ToolExecutionCardProps> = ({
  persona,
  tool,
  args,
  output,
  astSafe = true,
  requiresApproval = false,
  onApprove,
  onReject,
}) => {
  const [approvedState, setApprovedState] = useState<'pending' | 'approved' | 'rejected'>(
    requiresApproval ? 'pending' : 'approved'
  );

  const handleApprove = () => {
    setApprovedState('approved');
    onApprove?.();
  };

  const handleReject = () => {
    setApprovedState('rejected');
    onReject?.();
  };

  return (
    <div className="my-2 rounded-lg border border-slate-800 bg-slate-950/80 p-3 font-mono text-xs shadow-md">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <span className="text-amber-400">⚡ Tool Execution:</span>
          <span className="font-semibold text-slate-200">{tool}</span>
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400">by {persona}</span>
        </div>

        <div>
          {astSafe ? (
            <span className="inline-flex items-center gap-1 rounded bg-emerald-950/50 px-2 py-0.5 text-[10px] text-emerald-400 border border-emerald-800/50">
              ✓ AST Safe
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded bg-rose-950/50 px-2 py-0.5 text-[10px] text-rose-400 border border-rose-800/50">
              ⚠️ AST Warning
            </span>
          )}
        </div>
      </div>

      <div className="mt-2">
        <span className="text-[10px] uppercase tracking-wider text-slate-500">Arguments:</span>
        <pre className="mt-1 overflow-x-auto rounded bg-slate-900 p-2 text-[11px] text-slate-300">
          {JSON.stringify(args, null, 2)}
        </pre>
      </div>

      {requiresApproval && approvedState === 'pending' && (
        <div className="mt-3 rounded border border-amber-500/40 bg-amber-950/30 p-2.5">
          <div className="flex items-center gap-2 text-amber-300 font-medium">
            <span>🛡️ Guardrail Intercept:</span>
            <span>Manual User Confirmation Required</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-300">
            This tool action may modify local files or execute commands. Please confirm to proceed.
          </p>
          <div className="mt-2 flex gap-2">
            <button
              type="button"
              onClick={handleApprove}
              className="rounded bg-emerald-600 px-3 py-1 text-xs font-semibold text-white hover:bg-emerald-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-950"
            >
              Approve &amp; Run
            </button>
            <button
              type="button"
              onClick={handleReject}
              className="rounded bg-rose-600/80 px-3 py-1 text-xs font-semibold text-white hover:bg-rose-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-950"
            >
              Reject
            </button>
          </div>
        </div>
      )}

      {requiresApproval && approvedState === 'approved' && (
        <div className="mt-2 rounded border border-emerald-800/60 bg-emerald-950/40 px-2.5 py-1.5 text-[11px] font-medium text-emerald-300 flex items-center gap-1.5">
          <span>✓</span>
          <span>Guardrail Action Approved &amp; Executed</span>
        </div>
      )}

      {requiresApproval && approvedState === 'rejected' && (
        <div className="mt-2 rounded border border-rose-800/60 bg-rose-950/40 px-2.5 py-1.5 text-[11px] font-medium text-rose-300 flex items-center gap-1.5">
          <span>✕</span>
          <span>Guardrail Action Rejected</span>
        </div>
      )}

      {output && (
        <div className="mt-2">
          <span className="text-[10px] uppercase tracking-wider text-slate-500">Output:</span>
          <pre className="mt-1 overflow-x-auto rounded bg-slate-900/90 p-2 text-[11px] text-emerald-400">
            {output}
          </pre>
        </div>
      )}
    </div>
  );
};
