'use client';

import React, { useState } from 'react';

interface SynthesisCardProps {
  content: string;
  sessionId: string;
  isStreaming?: boolean;
  onStarForTraining?: () => void;
  stagedStatus?: boolean;
}

export const SynthesisCard: React.FC<SynthesisCardProps> = ({
  content,
  sessionId,
  isStreaming = false,
  onStarForTraining,
  stagedStatus = false,
}) => {
  const [starred, setStarred] = useState(stagedStatus);

  const handleStar = () => {
    setStarred(true);
    onStarForTraining?.();
  };

  return (
    <div className="my-4 rounded-xl border border-blue-500/30 bg-gradient-to-b from-blue-950/20 to-slate-950 p-4 shadow-lg">
      <div className="flex items-center justify-between border-b border-blue-500/20 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">👑</span>
          <div>
            <h4 className="font-semibold text-slate-100 text-sm">Supervisor Final Consensus (SakThai)</h4>
            <span className="text-[10px] text-slate-400 font-mono">Session ID: {sessionId}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {starred ? (
            <span className="inline-flex items-center gap-1 rounded bg-amber-950/60 px-2.5 py-1 text-xs font-medium text-amber-300 border border-amber-800/60">
              ⭐ Staged in LoRA Dataset Pool
            </span>
          ) : (
            <button
              type="button"
              onClick={handleStar}
              className="flex items-center gap-1 rounded-md bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-200 transition-all hover:bg-amber-600 hover:text-white"
            >
              <span>⭐</span>
              <span>Star for LoRA Training</span>
            </button>
          )}
        </div>
      </div>

      <div className="prose prose-invert max-w-none mt-3 text-xs leading-relaxed text-slate-200">
        <div className="whitespace-pre-wrap">{content}</div>
        {isStreaming && <span className="inline-block h-3 w-1.5 animate-pulse bg-blue-400 align-middle ml-1" />}
      </div>
    </div>
  );
};
