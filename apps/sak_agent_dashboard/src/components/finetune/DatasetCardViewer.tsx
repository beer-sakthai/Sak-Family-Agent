'use client';

import React, { useState } from 'react';
import { DatasetCardSpec } from '../../lib/types';

interface DatasetCardViewerProps {
  card: DatasetCardSpec;
  stagedCount: number;
}

export const DatasetCardViewer: React.FC<DatasetCardViewerProps> = ({ card, stagedCount }) => {
  const [selectedSampleIndex, setSelectedSampleIndex] = useState(0);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span>📦</span> Dataset Card: {card.name}
          </h3>
          <p className="text-xs text-slate-400 font-mono">Hugging Face Hub: {card.hfRepoId}</p>
        </div>

        <div className="flex gap-2">
          <span className="rounded bg-indigo-950 px-2 py-1 text-[11px] font-mono text-indigo-300 border border-indigo-800/50">
            {stagedCount} Staged Samples
          </span>
          <span className="rounded bg-slate-800 px-2 py-1 text-[11px] font-mono text-slate-300">
            Format: {card.format.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-[10px] uppercase text-slate-500">Total Samples</div>
          <div className="mt-1 text-base font-bold text-slate-200">{card.totalSamples}</div>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-[10px] uppercase text-slate-500">Avg Token Length</div>
          <div className="mt-1 text-base font-bold text-slate-200">{card.avgTokenLength} tokens</div>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-[10px] uppercase text-slate-500">Personas Covered</div>
          <div className="mt-1 text-xs font-semibold text-purple-300 truncate">
            {card.personasCovered.join(', ')}
          </div>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-[10px] uppercase text-slate-500">Target Hub Repo</div>
          <div className="mt-1 text-xs font-semibold text-blue-300 truncate">
            {card.hfRepoId}
          </div>
        </div>
      </div>

      {card.samples.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300 mb-2">
            <span>Sample Inspection ({selectedSampleIndex + 1} of {card.samples.length})</span>
            <div className="flex gap-1">
              {card.samples.map((_, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setSelectedSampleIndex(i)}
                  className={`h-5 w-5 rounded text-[10px] font-mono ${
                    selectedSampleIndex === i
                      ? 'bg-purple-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                  }`}
                >
                  {i + 1}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-950 p-3 font-mono text-[11px]">
            <div className="text-slate-400">
              <strong className="text-purple-400">&lt;|im_start|&gt;user</strong>
              <div className="mt-1 text-slate-200 whitespace-pre-wrap">
                {card.samples[selectedSampleIndex]?.instruction}
              </div>
              <strong className="text-purple-400">&lt;|im_end|&gt;</strong>
            </div>

            <div className="mt-3 text-slate-400 border-t border-slate-800/80 pt-2">
              <strong className="text-emerald-400">&lt;|im_start|&gt;assistant ({card.samples[selectedSampleIndex]?.persona})</strong>
              <div className="mt-1 text-slate-200 whitespace-pre-wrap">
                {card.samples[selectedSampleIndex]?.response}
              </div>
              <strong className="text-emerald-400">&lt;|im_end|&gt;</strong>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
