'use client';

import React from 'react';
import { LoraJobStatus } from '../../lib/types';

interface TrainingJobMonitorProps {
  jobs: LoraJobStatus[];
}

export const TrainingJobMonitor: React.FC<TrainingJobMonitorProps> = ({ jobs }) => {
  if (jobs.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-xs text-slate-500">
        No active or completed LoRA training jobs. Configure hyperparameters above to launch.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
        <span>📊</span> Active &amp; Recent Training Jobs ({jobs.length})
      </h3>

      <div className="grid grid-cols-1 gap-4">
        {jobs.map((job) => {
          const progressPct = Math.min(100, Math.round((job.currentStep / Math.max(1, job.totalSteps)) * 100));

          return (
            <div
              key={job.jobId}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 font-mono text-xs backdrop-blur shadow-sm"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-base">🚀</span>
                  <span className="font-bold text-slate-200">{job.modelName}</span>
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] text-slate-400">
                    ID: {job.jobId}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {job.status === 'running' && (
                    <span className="inline-flex items-center gap-1.5 rounded bg-blue-950 px-2.5 py-1 text-[11px] font-semibold text-blue-400 border border-blue-800/50 animate-pulse">
                      ● Training (Epoch {job.currentEpoch}/{job.totalEpochs})
                    </span>
                  )}
                  {job.status === 'completed' && (
                    <span className="inline-flex items-center gap-1.5 rounded bg-emerald-950 px-2.5 py-1 text-[11px] font-semibold text-emerald-400 border border-emerald-800/50">
                      ✓ Completed
                    </span>
                  )}
                  {job.status === 'failed' && (
                    <span className="inline-flex items-center gap-1.5 rounded bg-rose-950 px-2.5 py-1 text-[11px] font-semibold text-rose-400 border border-rose-800/50">
                      ✕ Failed
                    </span>
                  )}
                </div>
              </div>

              {/* Progress Gauge */}
              <div className="mt-3">
                <div className="flex justify-between text-[11px] text-slate-400">
                  <span>Step: {job.currentStep} / {job.totalSteps} ({progressPct}%)</span>
                  <span>Current Loss: <strong className="text-purple-300">{job.currentLoss}</strong></span>
                </div>
                <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-800">
                  <div
                    className={`h-full transition-all duration-500 ${
                      job.status === 'completed' ? 'bg-emerald-500' : 'bg-gradient-to-r from-purple-500 to-indigo-500'
                    }`}
                    style={{ width: `${progressPct}%` }}
                  />
                </div>
              </div>

              {/* Loss History Steps */}
              {job.lossHistory.length > 0 && (
                <div className="mt-3 rounded bg-slate-950/70 p-2.5">
                  <span className="text-[10px] uppercase tracking-wider text-slate-500">Loss Trajectory:</span>
                  <div className="mt-1 flex flex-wrap gap-2 text-[10px]">
                    {job.lossHistory.map((pt, i) => (
                      <span key={i} className="rounded bg-slate-900 px-2 py-0.5 text-slate-300">
                        E{pt.epoch} S{pt.step}: <span className="text-purple-400 font-bold">{pt.loss}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {job.checkpointPath && (
                <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/60 pt-2">
                  <span>Checkpoint: <code className="text-indigo-300">{job.checkpointPath}</code></span>
                  <span className="text-[10px] text-slate-500">
                    Started: {new Date(job.startedAt).toLocaleTimeString()}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
