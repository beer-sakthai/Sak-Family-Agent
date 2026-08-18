'use client';

import React, { useState } from 'react';
import { LoraTargetModel } from '../../lib/types';

interface TrainingConfigFormProps {
  onStartTraining: (config: {
    modelName: LoraTargetModel;
    r: number;
    loraAlpha: number;
    learningRate: number;
    numEpochs: number;
    batchSize: number;
  }) => Promise<void>;
  isSubmitting?: boolean;
}

export const TrainingConfigForm: React.FC<TrainingConfigFormProps> = ({
  onStartTraining,
  isSubmitting = false,
}) => {
  const [modelName, setModelName] = useState<LoraTargetModel>('sakthai-7b');
  const [r, setR] = useState(16);
  const [loraAlpha, setLoraAlpha] = useState(32);
  const [learningRate, setLearningRate] = useState(0.0002);
  const [numEpochs, setNumEpochs] = useState(3);
  const [batchSize, setBatchSize] = useState(4);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onStartTraining({
      modelName,
      r,
      loraAlpha,
      learningRate,
      numEpochs,
      batchSize,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
      <div className="mb-4 flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span>⚙️</span> LoRA Hyperparameter Configuration
          </h3>
          <p className="text-xs text-slate-400">Configure PEFT adapter rank, alpha, and training schedule.</p>
        </div>
        <span className="rounded bg-purple-950 px-2 py-0.5 text-[10px] font-mono text-purple-300 border border-purple-800/50">
          PEFT / PyTorch
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {/* Model Target */}
        <div>
          <label className="text-[11px] font-medium text-slate-300">Base Model Target</label>
          <select
            value={modelName}
            onChange={(e) => setModelName(e.target.value as LoraTargetModel)}
            className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:border-purple-500 focus:outline-none"
          >
            <option value="sakthai-7b">SakThai 7B (Mistral/Qwen Base)</option>
            <option value="sakthai-1.5b">SakThai 1.5B (Edge / Local CPU)</option>
            <option value="qwen-2.5-coder-7b">Qwen 2.5 Coder 7B</option>
          </select>
        </div>

        {/* LoRA Rank */}
        <div>
          <div className="flex justify-between text-[11px] font-medium text-slate-300">
            <span>LoRA Rank (r)</span>
            <span className="font-mono text-purple-400">{r}</span>
          </div>
          <input
            type="range"
            min="4"
            max="64"
            step="4"
            value={r}
            onChange={(e) => setR(Number(e.target.value))}
            className="mt-2 w-full accent-purple-500"
          />
        </div>

        {/* LoRA Alpha */}
        <div>
          <div className="flex justify-between text-[11px] font-medium text-slate-300">
            <span>LoRA Alpha (α)</span>
            <span className="font-mono text-purple-400">{loraAlpha}</span>
          </div>
          <input
            type="range"
            min="8"
            max="128"
            step="8"
            value={loraAlpha}
            onChange={(e) => setLoraAlpha(Number(e.target.value))}
            className="mt-2 w-full accent-purple-500"
          />
        </div>

        {/* Learning Rate */}
        <div>
          <label className="text-[11px] font-medium text-slate-300">Learning Rate</label>
          <input
            type="number"
            step="0.00005"
            min="0.00001"
            max="0.001"
            value={learningRate}
            onChange={(e) => setLearningRate(Number(e.target.value))}
            className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs font-mono text-slate-200 focus:border-purple-500 focus:outline-none"
          />
        </div>

        {/* Epochs */}
        <div>
          <label className="text-[11px] font-medium text-slate-300">Training Epochs</label>
          <input
            type="number"
            min="1"
            max="10"
            value={numEpochs}
            onChange={(e) => setNumEpochs(Number(e.target.value))}
            className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs font-mono text-slate-200 focus:border-purple-500 focus:outline-none"
          />
        </div>

        {/* Batch Size */}
        <div>
          <label className="text-[11px] font-medium text-slate-300">Batch Size per Device</label>
          <input
            type="number"
            min="1"
            max="16"
            value={batchSize}
            onChange={(e) => setBatchSize(Number(e.target.value))}
            className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs font-mono text-slate-200 focus:border-purple-500 focus:outline-none"
          />
        </div>
      </div>

      <div className="mt-5 flex justify-end">
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-md hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50"
        >
          <span>🔥</span>
          <span>{isSubmitting ? 'Spawning Job...' : 'Launch LoRA Fine-Tuning Job'}</span>
        </button>
      </div>
    </form>
  );
};
