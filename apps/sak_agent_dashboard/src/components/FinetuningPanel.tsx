'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { TrainingConfigForm } from './finetune/TrainingConfigForm';
import { TrainingJobMonitor } from './finetune/TrainingJobMonitor';
import { DatasetCardViewer } from './finetune/DatasetCardViewer';
import { DatasetCardSpec, LoraJobStatus, LoraTargetModel } from '../lib/types';

const DEFAULT_DATASET_CARD: DatasetCardSpec = {
  id: 'sakthai_combined_v7',
  name: 'SakThai Combined Instruction Dataset v7',
  format: 'chatml',
  totalSamples: 0,
  avgTokenLength: 256,
  personasCovered: ['sakthai', 'sakking', 'sakjules'],
  hfRepoId: 'Sak-Family/sakthai-combined-v7',
  samples: [],
};

const DEFAULT_JOBS: LoraJobStatus[] = [
  {
    jobId: 'job_baseline_sakthai_7b',
    modelName: 'sakthai-7b',
    status: 'completed',
    currentEpoch: 3,
    totalEpochs: 3,
    currentStep: 150,
    totalSteps: 150,
    lossHistory: [
      { epoch: 1, step: 50, loss: 1.84, evalLoss: 1.92 },
      { epoch: 2, step: 100, loss: 0.95, evalLoss: 1.04 },
      { epoch: 3, step: 150, loss: 0.42, evalLoss: 0.49 },
    ],
    currentLoss: 0.42,
    checkpointPath: 'checkpoints/sakthai-7b_lora_run1/final_adapter',
    startedAt: Date.now() - 3600000,
    completedAt: Date.now() - 600000,
  },
];

export const FinetuningPanel: React.FC = () => {
  const [datasetCard, setDatasetCard] = useState<DatasetCardSpec>(DEFAULT_DATASET_CARD);
  const [jobs, setJobs] = useState<LoraJobStatus[]>(DEFAULT_JOBS);
  const [stagedCount, setStagedCount] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadInitialData() {
      try {
        const res = await fetch('/api/learning/finetune');
        if (res.ok && isMounted) {
          const data = await res.json();
          if (data.datasetCard) setDatasetCard(data.datasetCard);
          if (data.jobs) setJobs(data.jobs);
          if (typeof data.stagedCount === 'number') setStagedCount(data.stagedCount);
        }
      } catch {
        // Fallback already populated
      }
    }

    loadInitialData();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleStartTraining = async (config: {
    modelName: LoraTargetModel;
    r: number;
    loraAlpha: number;
    learningRate: number;
    numEpochs: number;
    batchSize: number;
  }) => {
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await fetch('/api/learning/finetune', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || 'Failed to spawn training job');
      }

      const data = await res.json();
      if (data.job) {
        setJobs((prev) => [data.job, ...prev]);
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-slate-800 bg-gradient-to-r from-purple-950/40 via-slate-900/60 to-indigo-950/40 p-6 backdrop-blur">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">🧠</span>
              <h2 className="text-xl font-bold text-slate-100">LoRA Fine-Tuning &amp; Dataset Curation</h2>
              <span className="rounded-full bg-purple-500/20 px-2.5 py-0.5 text-xs font-semibold text-purple-300 border border-purple-500/30">
                Track 20260818
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-400 max-w-2xl">
              Closed-loop continuous training studio. Converts curated multi-agent session traces from the Chat
              Studio into Hugging Face dataset cards (<code>sakthai-combined-v7</code>) and triggers PEFT/LoRA fine-tuning
              for <strong>sakthai-1.5b</strong> and <strong>sakthai-7b</strong>.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 text-xs">
            <div className="rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-1.5 font-mono text-[11px] text-slate-300">
              <span className="text-slate-500">HF Hub:</span> <span className="text-purple-400">Connected</span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-1.5 font-mono text-[11px] text-slate-300">
              <span className="text-slate-500">Framework:</span> <span className="text-indigo-400">PEFT / PyTorch</span>
            </div>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-lg border border-rose-500/40 bg-rose-950/40 p-3 text-xs text-rose-300">
          ⚠️ {errorMsg}
        </div>
      )}

      {/* Dataset Card Viewer */}
      <DatasetCardViewer card={datasetCard} stagedCount={stagedCount} />

      {/* Hyperparameter Form */}
      <TrainingConfigForm onStartTraining={handleStartTraining} isSubmitting={isSubmitting} />

      {/* Training Monitor */}
      <TrainingJobMonitor jobs={jobs} />
    </div>
  );
};
