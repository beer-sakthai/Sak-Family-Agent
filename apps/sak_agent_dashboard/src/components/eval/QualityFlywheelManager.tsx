'use client';

import React, { useState } from 'react';
import { QualityFlywheelDataset, FlywheelFailureEntry } from '@/lib/eval/types';
import {
  RefreshCw,
  PlusCircle,
  Download,
  AlertTriangle,
  CheckCircle,
  Trash2,
  FolderGit2,
  SlidersHorizontal,
} from 'lucide-react';

interface QualityFlywheelManagerProps {
  datasets: QualityFlywheelDataset[];
  failures: FlywheelFailureEntry[];
  onTriageFailure?: (failureId: string, promoteToGolden: boolean) => void;
  onGenerateSynthetic?: (personaSlug: string) => void;
  onExportJsonl?: (datasetId: string) => void;
}

export const QualityFlywheelManager: React.FC<QualityFlywheelManagerProps> = ({
  datasets,
  failures,
  onTriageFailure,
  onGenerateSynthetic,
  onExportJsonl,
}) => {
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(datasets[0]?.id || '');
  const [activeTab, setActiveTab] = useState<'datasets' | 'triage'>('triage');

  const activeDataset = datasets.find((d) => d.id === selectedDatasetId) || datasets[0];
  const unreviewedFailures = failures.filter((f) => f.triageStatus === 'unreviewed');

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-6">
      {/* Top Header & Sub-Tab Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-emerald-400" />
            Quality Flywheel & Continuous Curation
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Turn runtime trace failures into golden regression benchmarks and curate multi-persona dataset splits.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab('triage')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'triage'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            Failure Triage ({unreviewedFailures.length})
          </button>
          <button
            onClick={() => setActiveTab('datasets')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'datasets'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FolderGit2 className="w-3.5 h-3.5" />
            Golden Datasets ({datasets.length})
          </button>
        </div>
      </div>

      {/* View: Failure Triage Queue */}
      {activeTab === 'triage' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Runtime Failures Requiring Review
            </span>
            <span className="text-xs text-slate-500">Active Learning Curation Loop</span>
          </div>

          {failures.length === 0 ? (
            <div className="text-center py-8 bg-slate-950/40 border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs">
              Zero failure incidents logged. All evaluations and runtime traces passing successfully!
            </div>
          ) : (
            <div className="space-y-3">
              {failures.map((fail) => {
                const isUnreviewed = fail.triageStatus === 'unreviewed';
                return (
                  <div
                    key={fail.id}
                    className={`p-4 rounded-lg border transition-all ${
                      isUnreviewed
                        ? 'bg-slate-950/80 border-slate-800 hover:border-slate-700'
                        : 'bg-slate-950/30 border-slate-900 opacity-60'
                    }`}
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-rose-950/70 border border-rose-800 text-rose-300">
                          {fail.failureCategory}
                        </span>
                        <span className="text-xs font-mono text-blue-400">[{fail.personaSlug}]</span>
                        <span className="text-xs text-slate-400 font-medium">Score: {fail.judgeScore} / 100</span>
                      </div>

                      <div className="flex items-center gap-2">
                        {isUnreviewed ? (
                          <>
                            <button
                              onClick={() => onTriageFailure?.(fail.id, true)}
                              className="px-2.5 py-1 bg-emerald-700 hover:bg-emerald-600 text-white rounded text-[11px] font-medium flex items-center gap-1 shadow-sm transition-colors"
                            >
                              <CheckCircle className="w-3 h-3" />
                              Promote to Golden Suite
                            </button>
                            <button
                              onClick={() => onGenerateSynthetic?.(fail.personaSlug)}
                              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[11px] font-medium flex items-center gap-1 border border-slate-700 transition-colors"
                            >
                              <PlusCircle className="w-3 h-3 text-amber-400" />
                              Synthetic Mutation
                            </button>
                            <button
                              onClick={() => onTriageFailure?.(fail.id, false)}
                              className="p-1 hover:bg-slate-800 text-slate-500 hover:text-slate-300 rounded"
                              title="Dismiss"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </>
                        ) : (
                          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-emerald-400 border border-emerald-800/40">
                            {fail.triageStatus}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="text-xs text-slate-200 font-medium">{fail.prompt}</div>
                    <div className="text-[11px] text-slate-400 mt-1 bg-slate-900/60 p-2 rounded border border-slate-800/60">
                      <span className="text-slate-500 font-mono">Trace Diagnostic:</span> {fail.traceSummary}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* View: Golden Datasets Browser */}
      {activeTab === 'datasets' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {datasets.map((ds) => {
              const isSelected = selectedDatasetId === ds.id;
              return (
                <div
                  key={ds.id}
                  onClick={() => setSelectedDatasetId(ds.id)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-slate-800 border-blue-500 ring-1 ring-blue-500/50'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-slate-200 truncate">{ds.name}</span>
                    <span className="text-[10px] font-mono bg-slate-900 px-1.5 py-0.5 rounded text-slate-400">
                      v{ds.version}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2">{ds.description}</p>
                  <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2 pt-2 border-t border-slate-800">
                    <span>{ds.testCases.length} Test Cases</span>
                    <span className="capitalize">Persona: {ds.persona}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {activeDataset && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">{activeDataset.name}</h4>
                  <span className="text-[10px] text-slate-500">Updated: {activeDataset.updatedAt}</span>
                </div>
                <button
                  onClick={() => onExportJsonl?.(activeDataset.id)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs font-medium flex items-center gap-1.5 border border-slate-700 shadow-sm transition-colors"
                >
                  <Download className="w-3.5 h-3.5 text-blue-400" />
                  Export .JSONL
                </button>
              </div>

              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {activeDataset.testCases.map((tc) => (
                  <div
                    key={tc.id}
                    className="p-2.5 bg-slate-900/60 rounded border border-slate-800/80 text-xs flex items-center justify-between"
                  >
                    <div>
                      <div className="font-medium text-slate-200 flex items-center gap-2">
                        <span>{tc.name}</span>
                        <span className="text-[10px] font-mono px-1 py-0.2 bg-slate-800 text-blue-400 rounded">
                          {tc.personaSlug}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 truncate max-w-lg mt-0.5">{tc.inputPrompt}</div>
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono text-right flex-shrink-0">
                      <span className="text-emerald-400 font-semibold">{tc.expectedTools.length} tools</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
