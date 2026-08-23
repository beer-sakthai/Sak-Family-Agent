'use client';

import React from 'react';
import { ChatStudio } from './chat/ChatStudio';

export const ChatStudioPanel: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-slate-800 bg-gradient-to-r from-blue-950/40 via-slate-900/60 to-purple-950/40 p-6 backdrop-blur">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">⚔️</span>
              <h2 className="text-xl font-bold text-slate-100">Collaborative Chat Arena &amp; Studio</h2>
              <span className="rounded-full bg-blue-500/20 px-2.5 py-0.5 text-xs font-semibold text-blue-300 border border-blue-500/30">
                Track 20260818
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-400 max-w-2xl">
              Real-time multi-agent collaborative workspace. <strong>SakThai</strong> coordinates task
              decomposition as supervisor, delegating sub-challenges to specialist personas with AST tool guardrails,
              live stdout/stderr streaming, and continuous LoRA dataset staging.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 text-xs">
            <div className="rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-1.5 font-mono text-[11px] text-slate-300">
              <span className="text-slate-500">Supervisor:</span> <span className="text-blue-400">SakThai</span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-1.5 font-mono text-[11px] text-slate-300">
              <span className="text-slate-500">AST Guardrails:</span> <span className="text-emerald-400">Enforced</span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-1.5 font-mono text-[11px] text-slate-300">
              <span className="text-slate-500">Staging:</span> <span className="text-amber-400">JSONL Pool</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Studio Shell */}
      <ChatStudio />
    </div>
  );
};
