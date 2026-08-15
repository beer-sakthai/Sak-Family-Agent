"use client";

import { useState } from "react";
import { SelfEvolutionData } from "@/lib/types";
import { getSelfEvolutionData } from "@/lib/selfEvolution";
import { RefreshCw, Sparkles, History, GitBranch, ArrowRight, ShieldCheck, CheckCircle2 } from "lucide-react";

export function SelfEvolutionPanel() {
  const [data] = useState<SelfEvolutionData>(getSelfEvolutionData());
  const [wrapping, setWrapping] = useState(false);
  const [wrapStatus, setWrapStatus] = useState<string | null>(null);

  const handleTriggerCycleWrap = () => {
    setWrapping(true);
    setWrapStatus(null);
    setTimeout(() => {
      setWrapping(false);
      setWrapStatus("🚀 Continuous Self-Evolution Loop completed successfully! Wrapped Growth ➔ Dream stage (Round 5 ready).");
    }, 1200);
  };

  return (
    <section className="space-y-6" data-testid="self-evolution-panel">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-rose-950/40 via-rose-900/20 to-zinc-900 border border-rose-800/40 rounded-xl p-5 backdrop-blur-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">
              Growth Stage · 6.0
            </span>
            <span className="text-xs text-zinc-400">Lead: SakJules (Master of CI/CD)</span>
          </div>
          <h2 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
            <RefreshCw className="w-6 h-6 text-rose-400" />
            Self-Evolution & Continuous Learning Loop
          </h2>
          <p className="text-sm text-zinc-400 mt-1 max-w-2xl">
            Automated prompt refinement diffs, learning journal capture, and autonomous cycle wrap-back execution.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-zinc-900/80 border border-zinc-800 px-3.5 py-2 rounded-lg text-center">
            <div className="text-xl font-bold text-rose-400">Round {data.round}</div>
            <div className="text-[11px] text-zinc-400 font-medium uppercase tracking-wider">Evolution Cycle</div>
          </div>
          <div className="bg-zinc-900/80 border border-zinc-800 px-3.5 py-2 rounded-lg text-center">
            <div className="text-xl font-bold text-emerald-400">{data.mutationCoveragePct}%</div>
            <div className="text-[11px] text-zinc-400 font-medium uppercase tracking-wider">Mutation Score</div>
          </div>
        </div>
      </div>

      {/* Trigger Button & Status */}
      <div className="bg-zinc-900/80 border border-rose-900/40 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold text-zinc-200">Autonomous Cycle Wrap Trigger</div>
            <div className="text-[11px] text-zinc-400">
              Executes end-to-end feedback loop (Dream ➔ Hope ➔ Care ➔ Joy ➔ Trust ➔ Growth ➔ Dream).
            </div>
          </div>
        </div>

        <button
          onClick={handleTriggerCycleWrap}
          disabled={wrapping}
          className="py-2 px-4 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs flex items-center gap-2 transition-all shadow-md shadow-rose-600/20 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${wrapping ? "animate-spin" : ""}`} />
          {wrapping ? "Executing Evolution Cycle..." : "Trigger Autonomous Wrap"}
        </button>
      </div>

      {wrapStatus && (
        <div className="p-3 bg-zinc-950 border border-rose-800/40 rounded-xl text-xs font-mono text-emerald-400 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          {wrapStatus}
        </div>
      )}

      {/* Prompt Evolution Diffs */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-rose-400" />
          Persona Prompt Evolution Diffs
        </h3>

        <div className="space-y-3">
          {data.evolutions.map((evo) => (
            <div
              key={evo.id}
              className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 space-y-3"
            >
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-zinc-200 uppercase">{evo.personaSlug} Prompt Refinement</span>
                <span className="text-emerald-400 font-semibold text-[11px]">{evo.performanceDelta}</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 rounded bg-zinc-950 border border-rose-900/30">
                  <div className="text-[10px] uppercase font-bold text-rose-400 mb-1">Baseline Prompt</div>
                  <div className="font-mono text-zinc-400 text-[11px]">{evo.originalSnippet}</div>
                </div>
                <div className="p-2.5 rounded bg-zinc-950 border border-emerald-900/30">
                  <div className="text-[10px] uppercase font-bold text-emerald-400 mb-1">Evolved Prompt (Self-Learned)</div>
                  <div className="font-mono text-zinc-200 text-[11px]">{evo.evolvedSnippet}</div>
                </div>
              </div>

              <div className="text-[11px] text-zinc-400 flex items-center gap-1.5">
                <span className="font-semibold text-zinc-300">Rationale:</span>
                {evo.rationale}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Learning Journal History */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
          <History className="w-4 h-4 text-zinc-400" />
          Recent Continuous Learning Journal Log (`learning_journal.jsonl`)
        </h3>

        <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl divide-y divide-zinc-800/60 overflow-hidden">
          {data.journalEntries.map((entry) => (
            <div key={entry.id} className="p-3.5 flex items-start justify-between gap-3 text-xs">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-zinc-200">{entry.persona}</span>
                  <span className="text-[10px] text-zinc-400">Trigger: {entry.triggerEvent}</span>
                </div>
                <p className="text-[11px] text-zinc-400 mt-1">{entry.lessonLearned}</p>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-semibold border border-emerald-500/20 shrink-0">
                Remediated
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
