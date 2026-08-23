'use client';

import React, { useState } from 'react';
import { EvalRunResult, EvalTestCase } from '@/lib/eval/types';
import {
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  ShieldCheck,
  Wrench,
  ChevronDown,
  ChevronRight,
  Zap,
} from 'lucide-react';

interface EvalRunTrackerProps {
  isRunning: boolean;
  results: EvalRunResult[];
  availableTestCases: EvalTestCase[];
  onTriggerRun?: (selectedIds: string[]) => void;
}

export const EvalRunTracker: React.FC<EvalRunTrackerProps> = ({
  isRunning,
  results,
  availableTestCases,
  onTriggerRun,
}) => {
  const [selectedCaseIds, setSelectedCaseIds] = useState<string[]>(
    availableTestCases.map((t) => t.id)
  );
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);

  const toggleSelectCase = (id: string) => {
    setSelectedCaseIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const selectAll = () => setSelectedCaseIds(availableTestCases.map((t) => t.id));
  const deselectAll = () => setSelectedCaseIds([]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-6">
      {/* Run Header & Quick Launcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-400" />
            Evaluation Arena & Automated Runner
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Execute standardized benchmark suites against all 6 Sak-Family personas with LLM-as-a-Judge scoring.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={selectAll}
            className="text-xs text-slate-400 hover:text-slate-200 px-2 py-1 bg-slate-800 rounded border border-slate-700"
          >
            Select All
          </button>
          <button
            onClick={deselectAll}
            className="text-xs text-slate-400 hover:text-slate-200 px-2 py-1 bg-slate-800 rounded border border-slate-700"
          >
            Clear
          </button>
          <button
            onClick={() => onTriggerRun?.(selectedCaseIds)}
            disabled={isRunning || selectedCaseIds.length === 0}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all shadow-md ${
              isRunning || selectedCaseIds.length === 0
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-500 text-white hover:shadow-blue-500/20'
            }`}
          >
            {isRunning ? (
              <>
                <Clock className="w-4 h-4 animate-spin text-blue-300" />
                Evaluating Test Matrix...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 text-amber-300" />
                Run Selected ({selectedCaseIds.length})
              </>
            )}
          </button>
        </div>
      </div>

      {/* Test Case Selection Chips */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-slate-400">Available Benchmark Test Cases:</label>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
          {availableTestCases.map((tc) => {
            const isSelected = selectedCaseIds.includes(tc.id);
            return (
              <div
                key={tc.id}
                onClick={() => toggleSelectCase(tc.id)}
                className={`p-2.5 rounded-lg border text-left cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-blue-950/40 border-blue-600/70 text-slate-200'
                    : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase bg-slate-800 px-1.5 py-0.5 rounded text-blue-400">
                    {tc.personaSlug}
                  </span>
                  <span className="text-[10px] text-slate-400">{tc.category}</span>
                </div>
                <div className="text-xs font-medium mt-1 truncate">{tc.name}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live / Recent Evaluation Results List */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Evaluation Run Trajectories</h4>
          <span className="text-xs text-slate-500">{results.length} runs recorded</span>
        </div>

        {results.length === 0 ? (
          <div className="text-center py-8 bg-slate-950/40 border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs">
            No evaluation runs recorded yet. Click &quot;Run Selected&quot; above to execute the benchmark matrix.
          </div>
        ) : (
          <div className="space-y-2.5">
            {results.map((run) => {
              const isExpanded = expandedRunId === run.id;
              const isPass = run.judgeScore?.passed ?? false;
              const composite = run.judgeScore?.compositeScore ?? 0;

              return (
                <div
                  key={run.id}
                  className="border border-slate-800 bg-slate-950/70 rounded-lg overflow-hidden transition-all"
                >
                  {/* Header Row */}
                  <div
                    onClick={() => setExpandedRunId(isExpanded ? null : run.id)}
                    className="p-3 flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {isPass ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                      ) : (
                        <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
                      )}
                      <div>
                        <div className="text-xs font-semibold text-slate-200 flex items-center gap-2">
                          <span>{run.testCaseName}</span>
                          <span className="text-[10px] px-1.5 py-0.2 bg-slate-800 text-blue-400 font-mono rounded">
                            {run.personaSlug}
                          </span>
                        </div>
                        <div className="text-[10px] text-slate-400 flex items-center gap-3 mt-0.5">
                          <span>⏱️ {run.executionTimeMs}ms</span>
                          <span>🪙 {run.tokensUsed.total} tokens</span>
                          <span>🔄 {run.traces.length} steps</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className={`text-xs font-bold ${isPass ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {composite} / 100
                        </div>
                        <div className="text-[10px] text-slate-400">{isPass ? 'PASSED' : 'FAILED'}</div>
                      </div>
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Detail View */}
                  {isExpanded && (
                    <div className="p-4 bg-slate-900/90 border-t border-slate-800 space-y-4 text-xs">
                      {/* LLM-as-a-Judge CoT Reasoning */}
                      {run.judgeScore && (
                        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-blue-400 flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5" />
                              LLM-as-a-Judge Diagnostic Chain-of-Thought
                            </span>
                            <span className="text-[10px] text-slate-500 font-mono">G-Eval Framework</span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-slate-300 pt-1">
                            <div className="p-2 bg-slate-900 rounded border border-slate-800">
                              <span className="font-semibold text-slate-400">Goal Completion ({run.judgeScore.goalCompletion}%):</span>{' '}
                              {run.judgeScore.reasoning.goalAnalysis}
                            </div>
                            <div className="p-2 bg-slate-900 rounded border border-slate-800">
                              <span className="font-semibold text-slate-400">Tool Precision ({run.judgeScore.toolPrecision}%):</span>{' '}
                              {run.judgeScore.reasoning.toolAnalysis}
                            </div>
                            <div className="p-2 bg-slate-900 rounded border border-slate-800">
                              <span className="font-semibold text-slate-400">AST Guardrail ({run.judgeScore.safetyCompliance}%):</span>{' '}
                              {run.judgeScore.reasoning.safetyAnalysis}
                            </div>
                            <div className="p-2 bg-slate-900 rounded border border-slate-800">
                              <span className="font-semibold text-slate-400">Efficiency ({run.judgeScore.latencyCost}%):</span>{' '}
                              {run.judgeScore.reasoning.efficiencyAnalysis}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Step-by-Step Trajectory Logs */}
                      <div className="space-y-1.5">
                        <span className="font-semibold text-slate-400 text-[11px]">Execution Trajectory Traces:</span>
                        {run.traces.map((trace) => (
                          <div
                            key={trace.stepNumber}
                            className="p-2.5 bg-slate-950/60 rounded border border-slate-800/70 text-[11px] space-y-1"
                          >
                            <div className="flex items-center justify-between text-slate-400 font-mono text-[10px]">
                              <span>Step #{trace.stepNumber}</span>
                              <span>{trace.latencyMs}ms</span>
                            </div>
                            <div className="text-slate-300 font-sans">{trace.thought}</div>

                            {trace.toolCall && (
                              <div className="bg-slate-900 p-2 rounded border border-slate-800 font-mono text-[10px] text-amber-300 flex items-center gap-2">
                                <Wrench className="w-3 h-3 text-amber-400" />
                                <span>Tool Call: {trace.toolCall.name}()</span>
                              </div>
                            )}

                            {trace.output && (
                              <div className="bg-slate-900/80 p-2 rounded border border-emerald-800/40 text-emerald-300 text-[11px]">
                                <ShieldCheck className="w-3 h-3 inline mr-1 text-emerald-400" />
                                {trace.output}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
