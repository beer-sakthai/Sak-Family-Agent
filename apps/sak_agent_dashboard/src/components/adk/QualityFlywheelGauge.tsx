'use client';

import React from 'react';
import { QualityFlywheelEvalResult } from '../../lib/types';

interface QualityFlywheelGaugeProps {
  evalResult: QualityFlywheelEvalResult;
  onRunEval?: () => Promise<void>;
  isRunning?: boolean;
}

export const QualityFlywheelGauge: React.FC<QualityFlywheelGaugeProps> = ({
  evalResult,
  onRunEval,
  isRunning = false,
}) => {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span>🎯</span> Quality Flywheel &amp; LLM-as-Judge Evaluation
          </h3>
          <p className="text-xs text-slate-400">
            Automated benchmark harness scoring accuracy, tool calling precision, latency, and AST safety.
          </p>
        </div>

        <button
          type="button"
          onClick={onRunEval}
          disabled={isRunning}
          className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          <span>{isRunning ? '⏳ Running Flywheel Eval...' : '⚡ Run Quality Eval'}</span>
        </button>
      </div>

      {/* 4 Core Summary Cards */}
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-[10px] uppercase text-slate-500">Overall Accuracy</div>
          <div className="mt-1 text-xl font-bold text-emerald-400">{evalResult.overallAccuracy}%</div>
          <span className="text-[10px] text-slate-400">Target: ≥90%</span>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-[10px] uppercase text-slate-500">Tool Calling Precision</div>
          <div className="mt-1 text-xl font-bold text-blue-400">{evalResult.toolCallingPrecision}%</div>
          <span className="text-[10px] text-slate-400">Target: ≥90%</span>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-[10px] uppercase text-slate-500">Average Latency</div>
          <div className="mt-1 text-xl font-bold text-purple-400">{evalResult.avgLatencyMs} ms</div>
          <span className="text-[10px] text-slate-400">Tokens/sec: 84.5</span>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-[10px] uppercase text-slate-500">Safety Compliance</div>
          <div className="mt-1 text-xl font-bold text-teal-400">{evalResult.safetyCompliance}%</div>
          <span className="text-[10px] text-slate-400">0 AST violations</span>
        </div>
      </div>

      {/* Detailed Metrics Category Breakdown */}
      <div className="mt-5 space-y-3">
        <h4 className="text-xs font-semibold text-slate-300">Category Evaluation Breakdown</h4>
        {evalResult.metrics.map((metric) => (
          <div key={metric.category} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-slate-300">{metric.category}</span>
              <span className="font-mono text-emerald-400 font-bold">
                {metric.score}% <span className="text-slate-500 text-[10px]">(Target: {metric.benchmarkTarget}%)</span>
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-950 border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-400"
                style={{ width: `${metric.score}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
