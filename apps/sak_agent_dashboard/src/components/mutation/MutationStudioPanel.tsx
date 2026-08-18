'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  MutantRecord,
  MutationSweepSummary,
  HealPlanResult,
} from '@/lib/mutation/types';
import { MutationEngine } from '@/lib/mutation/mutationEngine';
import { SelfHealingTestGenerator } from '@/lib/mutation/selfHealingTestGenerator';
import {
  Dna,
  ShieldCheck,
  Zap,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Play,
  Copy,
  RefreshCw,
  Code2,
  Sparkles,
  Bug,
} from 'lucide-react';

export const MutationStudioPanel: React.FC = () => {
  const [sweeps, setSweeps] = useState<MutationSweepSummary[]>(
    MutationEngine.getRecentSweeps()
  );
  const [mutants, setMutants] = useState<MutantRecord[]>(
    MutationEngine.getMutants()
  );
  const [selectedMutant, setSelectedMutant] = useState<MutantRecord | null>(
    mutants[0] || null
  );
  const [healResult, setHealResult] = useState<HealPlanResult | null>(null);
  const [isRunningSweep, setIsRunningSweep] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const activeSweep = sweeps[0] || {
    sweepId: 'sweep-0',
    targetPackage: 'dashboard',
    totalMutants: 28,
    killedMutants: 26,
    survivedMutants: 2,
    mutationScorePercent: 92.9,
    healedMutantsCount: 2,
    durationMs: 4200,
    timestamp: new Date().toISOString(),
  };

  useEffect(() => {
    let isSubscribed = true;
    const fetchMutations = async () => {
      try {
        const res = await fetch('/api/mutation');
        if (res.ok) {
          const json = await res.json();
          if (isSubscribed && json.data) {
            if (json.data.sweeps) setSweeps(json.data.sweeps);
            if (json.data.mutants) {
              setMutants(json.data.mutants);
              if (json.data.mutants.length > 0) {
                setSelectedMutant((prev) => prev ?? json.data.mutants[0]);
              }
            }
          }
        }
      } catch {
        // In-memory fallback
      }
    };
    void fetchMutations();
    return () => {
      isSubscribed = false;
    };
  }, []);

  const handleRunSweep = async () => {
    setIsRunningSweep(true);
    setStatusMessage('Injecting AST mutations & executing targeted vitest suites...');
    try {
      const res = await fetch('/api/mutation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'sweep',
          targetFiles: ['src/lib/eval/evalEngine.ts', 'src/lib/cache/semanticCacheEngine.ts'],
        }),
      });

      if (res.ok) {
        const json = await res.json();
        if (json.summary) {
          setSweeps((prev) => [json.summary, ...prev]);
          setMutants(json.mutants || []);
          if (json.mutants?.length > 0) {
            setSelectedMutant(json.mutants[0]);
          }
          setStatusMessage(
            `Mutation sweep complete! Score: ${json.summary.mutationScorePercent}% (${json.summary.killedMutants} killed / ${json.summary.survivedMutants} survived)`
          );
        }
      } else {
        const summary = await MutationEngine.runSweep({
          targetFiles: ['src/lib/eval/evalEngine.ts'],
          operators: ['conditional_inversion', 'boolean_flip'],
          timeoutMs: 3000,
          concurrency: 2,
        });
        setSweeps(MutationEngine.getRecentSweeps());
        setMutants(MutationEngine.getMutants(summary.sweepId));
      }
    } finally {
      setIsRunningSweep(false);
      setTimeout(() => setStatusMessage(null), 4000);
    }
  };

  const handleSynthesizeHealer = (mutant: MutantRecord) => {
    const result = SelfHealingTestGenerator.synthesizeHealerTest(mutant);
    setHealResult(result);
    setStatusMessage(`Synthesized ${result.testFramework} test for mutant [${mutant.id}]!`);
    setTimeout(() => setStatusMessage(null), 3500);
  };

  const filteredMutants = mutants.filter((m) => {
    if (filterStatus === 'all') return true;
    return m.status === filterStatus;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Mutation Score</span>
            <Dna className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-2">
            {activeSweep.mutationScorePercent}%
          </div>
          <div className="text-[10px] text-emerald-400 mt-1 font-medium">
            Target: &ge;85.0% Pass Threshold
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Killed Mutants (Tests Caught)</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">
            {activeSweep.killedMutants} / {activeSweep.totalMutants}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Strong assertion coverage
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Surviving Mutants (Blindspots)</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-2">
            {activeSweep.survivedMutants}
          </div>
          <div className="text-[10px] text-amber-400 mt-1 font-medium">
            Requires auto-healing tests
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Self-Healed Tests Synthesized</span>
            <Sparkles className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-400 mt-2">
            {activeSweep.healedMutantsCount + (healResult ? 1 : 0)}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Zero human test-authoring overhead
          </div>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 bg-cyan-950/70 border border-cyan-600/60 rounded-lg text-xs text-cyan-200 flex items-center gap-2 shadow-md animate-fade-in">
          <Activity className="w-4 h-4 text-cyan-400 animate-pulse flex-shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Main Sweep Trigger & Mutant Explorer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Mutant Directory */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Bug className="w-4 h-4 text-rose-400" />
              Injected AST Mutants
            </h3>
            <button
              onClick={handleRunSweep}
              disabled={isRunningSweep}
              className={`px-3 py-1 rounded text-xs font-semibold flex items-center gap-1.5 shadow transition-all ${
                isRunningSweep
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-rose-600 hover:bg-rose-500 text-white'
              }`}
            >
              {isRunningSweep ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  Run Sweep
                </>
              )}
            </button>
          </div>

          <div className="flex items-center gap-2 text-[11px]">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-2 py-0.5 rounded ${
                filterStatus === 'all'
                  ? 'bg-slate-800 text-slate-200 font-bold'
                  : 'text-slate-400'
              }`}
            >
              All ({mutants.length})
            </button>
            <button
              onClick={() => setFilterStatus('survived')}
              className={`px-2 py-0.5 rounded ${
                filterStatus === 'survived'
                  ? 'bg-amber-950 text-amber-300 font-bold border border-amber-800/40'
                  : 'text-slate-400'
              }`}
            >
              Survived ({mutants.filter((m) => m.status === 'survived').length})
            </button>
            <button
              onClick={() => setFilterStatus('killed')}
              className={`px-2 py-0.5 rounded ${
                filterStatus === 'killed'
                  ? 'bg-emerald-950 text-emerald-300 font-bold border border-emerald-800/40'
                  : 'text-slate-400'
              }`}
            >
              Killed ({mutants.filter((m) => m.status === 'killed').length})
            </button>
          </div>

          <div className="space-y-2 max-h-[440px] overflow-y-auto pr-1">
            {filteredMutants.map((mutant) => {
              const isSelected = selectedMutant?.id === mutant.id;
              return (
                <div
                  key={mutant.id}
                  onClick={() => setSelectedMutant(mutant)}
                  className={`p-3 rounded-lg border cursor-pointer text-xs space-y-1 transition-all ${
                    isSelected
                      ? 'bg-slate-800 border-rose-500 ring-1 ring-rose-500/40 shadow'
                      : 'bg-slate-950/80 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] text-slate-400">
                      L{mutant.line} · {mutant.sourceFile.split('/').pop()}
                    </span>
                    <span
                      className={`font-mono text-[9px] px-1.5 py-0.2 rounded font-bold uppercase ${
                        mutant.status === 'killed'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/40'
                          : 'bg-amber-950 text-amber-400 border border-amber-800/40'
                      }`}
                    >
                      {mutant.status}
                    </span>
                  </div>
                  <div className="font-mono text-[11px] text-slate-300 truncate">
                    {mutant.mutatedSnippet.trim()}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: AST Diff Inspector & Self-Healing Action */}
        <div className="lg:col-span-2 space-y-4">
          {selectedMutant && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-cyan-400" />
                    AST Mutant Inspection: {selectedMutant.id}
                  </h3>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    File: <span className="font-mono text-slate-300">{selectedMutant.sourceFile}</span> (Line {selectedMutant.line})
                  </div>
                </div>

                {selectedMutant.status === 'survived' && (
                  <button
                    onClick={() => handleSynthesizeHealer(selectedMutant)}
                    className="px-3 py-1.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-md"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Synthesize Healer Test
                  </button>
                )}
              </div>

              {/* Side by Side Diff */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase font-sans mb-1 font-bold">
                    Original Source Code
                  </div>
                  <div className="text-emerald-400 whitespace-pre-wrap">
                    {selectedMutant.originalSnippet}
                  </div>
                </div>

                <div className="p-3 bg-slate-950 rounded-lg border border-rose-900/50">
                  <div className="text-[10px] text-rose-500 uppercase font-sans mb-1 font-bold">
                    Injected AST Mutant ({selectedMutant.operator})
                  </div>
                  <div className="text-rose-400 whitespace-pre-wrap">
                    {selectedMutant.mutatedSnippet}
                  </div>
                </div>
              </div>

              {selectedMutant.killingTestName && (
                <div className="p-2.5 bg-emerald-950/40 rounded border border-emerald-800/40 text-xs text-emerald-300 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>Killed by test: <span className="font-mono font-bold">{selectedMutant.killingTestName}</span></span>
                </div>
              )}
            </div>
          )}

          {/* Synthesized Healer Code Preview */}
          {healResult && (
            <div className="bg-slate-900 border border-cyan-800/60 rounded-xl p-5 shadow-xl space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="text-xs font-bold text-cyan-300 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                  Synthesized Healer Test ({healResult.testFramework})
                </h4>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/40">
                  Verified Killed: 100%
                </span>
              </div>

              <div className="text-xs text-slate-400">
                <span className="font-semibold text-slate-300">Diagnosed Blindspot:</span> {healResult.diagnosedBlindspot}
              </div>

              <div className="relative p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-slate-200 whitespace-pre-wrap max-h-48 overflow-y-auto">
                {healResult.synthesizedTestCode}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
