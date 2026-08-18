"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  AlertTriangle,
  Check,
  Copy,
  Crown,
  FlaskConical,
  Heart,
  Layers,
  Lightbulb,
  RefreshCw,
  Rocket,
  ShieldCheck,
  Smile,
  Sparkles,
  Terminal,
  Users,
  Play,
  RotateCcw,
  ArrowRight,
  Activity,
  FileCode2,
} from "lucide-react";
import { AutoCycleData, CycleStage, PersonaCycleState, CycleStageName } from "@/lib/types";
import { CycleEngine } from "@/lib/cycle/cycleEngine";

interface AutoCyclePanelProps {
  data: AutoCycleData | null;
}

const STAGE_ICON: Record<string, React.ReactNode> = {
  dream: <Lightbulb className="h-4 w-4 text-purple-300" />,
  hope: <Sparkles className="h-4 w-4 text-cyan-300" />,
  care: <Heart className="h-4 w-4 text-rose-300" />,
  joy: <Smile className="h-4 w-4 text-amber-300" />,
  trust: <ShieldCheck className="h-4 w-4 text-emerald-300" />,
  growth: <Rocket className="h-4 w-4 text-sky-300" />,
};

const STAGE_ACCENT: Record<string, string> = {
  dream: "border-purple-500/40 bg-purple-500/[0.06]",
  hope: "border-cyan-500/40 bg-cyan-500/[0.06]",
  care: "border-rose-500/40 bg-rose-500/[0.06]",
  joy: "border-amber-500/40 bg-amber-500/[0.06]",
  trust: "border-emerald-500/40 bg-emerald-500/[0.06]",
  growth: "border-sky-500/40 bg-sky-500/[0.06]",
};

function CopyButton({ payload }: { payload: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(payload);
      }
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };
  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/60 text-slate-300 hover:text-white hover:border-cyan-500/40 transition-colors"
    >
      {copied ? (
        <>
          <Check className="h-3.5 w-3.5 text-emerald-400" /> Copied
        </>
      ) : (
        <>
          <Copy className="h-3.5 w-3.5 text-cyan-400" /> Copy
        </>
      )}
    </button>
  );
}

export default function AutoCyclePanel({ data }: AutoCyclePanelProps) {
  const [selectedPersona, setSelectedPersona] = useState<string>("SakThai");
  const [personaStates, setPersonaStates] = useState<Record<string, PersonaCycleState>>(
    CycleEngine.getAllPersonaStates()
  );
  const [customTask, setCustomTask] = useState<string>("");
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [statusLog, setStatusLog] = useState<string | null>(null);

  const activeState = personaStates[selectedPersona] || CycleEngine.getPersonaState(selectedPersona);

  const loadData = useCallback(async () => {
    try {
      const res = await fetch("/api/auto-cycle");
      if (res.ok) {
        const json = await res.json();
        if (json.cycleStates) {
          setPersonaStates(json.cycleStates);
        }
      }
    } catch {
      // In-memory fallback
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStepStage = async () => {
    setIsExecuting(true);
    setStatusLog(`[${selectedPersona}] Executing stage [${activeState.currentStage.toUpperCase()}]...`);
    try {
      const res = await fetch("/api/auto-cycle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "step",
          persona: selectedPersona,
          task: customTask.trim() || undefined,
        }),
      });

      if (res.ok) {
        const json = await res.json();
        if (json.state) {
          setPersonaStates((prev) => ({ ...prev, [selectedPersona]: json.state }));
          if (json.stepResult?.logMessage) {
            setStatusLog(json.stepResult.logMessage);
          }
        }
      } else {
        const result = await CycleEngine.stepStage(selectedPersona, customTask.trim() || undefined);
        setPersonaStates(CycleEngine.getAllPersonaStates());
        setStatusLog(result.logMessage);
      }
    } finally {
      setIsExecuting(false);
    }
  };

  const handleRunRound = async () => {
    setIsExecuting(true);
    setStatusLog(`[${selectedPersona}] Running full 6-stage autonomous cycle...`);
    try {
      const res = await fetch("/api/auto-cycle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "run_round",
          persona: selectedPersona,
          task: customTask.trim() || undefined,
        }),
      });

      if (res.ok) {
        const json = await res.json();
        if (json.state) {
          setPersonaStates((prev) => ({ ...prev, [selectedPersona]: json.state }));
          setStatusLog(`[${selectedPersona}] Completed full round (Round ${json.state.currentRound}/${json.state.maxRounds})`);
        }
      } else {
        await CycleEngine.runFullCycle(selectedPersona, customTask.trim() || undefined);
        setPersonaStates(CycleEngine.getAllPersonaStates());
        setStatusLog(`[${selectedPersona}] Completed full autonomous round`);
      }
    } finally {
      setIsExecuting(false);
    }
  };

  const handleReset = async () => {
    const newState = CycleEngine.resetCycle(selectedPersona);
    setPersonaStates((prev) => ({ ...prev, [selectedPersona]: newState }));
    setStatusLog(`[${selectedPersona}] Cycle reset to Round 1, Stage DREAM.`);
    setTimeout(() => setStatusLog(null), 3000);
  };

  const STAGES_LIST: CycleStageName[] = ['dream', 'hope', 'care', 'joy', 'trust', 'growth'];

  return (
    <div className="space-y-6">
      {/* Top Banner Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-purple-950/40 via-slate-900/60 to-cyan-950/40 border border-slate-800 backdrop-blur-xl shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">🔄</span>
              <h2 className="text-xl font-bold text-slate-100 font-display">
                6-Part Cycle Intelligence &amp; Operations Suite
              </h2>
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold">
                Observe-Orient-Decide-Act-Learn
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
              Autonomous multi-agent execution loop across all 6 Sak-Family personas.
              Advances from <strong>Dream (Vision)</strong> to <strong>Growth (Consolidation)</strong> with per-stage artifact generation and memory persistence.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-right">
              <div className="text-[10px] text-slate-500 font-mono uppercase">Round Status</div>
              <div className="text-base font-bold text-cyan-400 font-mono">
                Round {activeState.currentRound} / {activeState.maxRounds}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-right">
              <div className="text-[10px] text-slate-500 font-mono uppercase">Active Stage</div>
              <div className="text-base font-bold text-purple-300 font-mono uppercase">
                {activeState.currentStage}
              </div>
            </div>
          </div>
        </div>
      </div>

      {statusLog && (
        <div className="p-3 bg-cyan-950/70 border border-cyan-600/60 rounded-lg text-xs text-cyan-200 flex items-center gap-2 shadow-md animate-fade-in">
          <Activity className="w-4 h-4 text-cyan-400 animate-pulse flex-shrink-0" />
          <span className="font-mono">{statusLog}</span>
        </div>
      )}

      {/* Persona Selection Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {CycleEngine.DEFAULT_PERSONAS.map((persona) => {
          const isSelected = persona === selectedPersona;
          const pState = personaStates[persona] || CycleEngine.getPersonaState(persona);
          return (
            <div
              key={persona}
              onClick={() => setSelectedPersona(persona)}
              className={`p-3 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? "bg-purple-950/40 border-purple-500 ring-1 ring-purple-500/40 shadow-lg"
                  : "bg-slate-900/80 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs text-slate-200">{persona}</span>
                {persona === "SakThai" && (
                  <Crown className="w-3.5 h-3.5 text-amber-400" />
                )}
              </div>
              <div className="text-[10px] font-mono text-purple-400 mt-1 uppercase font-bold">
                Stage: {pState.currentStage}
              </div>
              <div className="text-[10px] text-slate-500 font-mono">
                R{pState.currentRound}/{pState.maxRounds} · {pState.status}
              </div>
            </div>
          );
        })}
      </div>

      {/* Cycle Stage Dial Visualizer */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              Continuous Intelligence Flow: {selectedPersona}
            </h3>
            <div className="text-[11px] text-slate-400 mt-0.5 truncate max-w-xl">
              Task: <span className="text-slate-300 font-mono">{activeState.activeTask || "Autonomous Monorepo Verification"}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleStepStage}
              disabled={isExecuting}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow transition-all ${
                isExecuting
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                  : "bg-cyan-600 hover:bg-cyan-500 text-white"
              }`}
            >
              {isExecuting ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Advancing...
                </>
              ) : (
                <>
                  <ArrowRight className="w-3.5 h-3.5" />
                  Step Next Stage
                </>
              )}
            </button>

            <button
              onClick={handleRunRound}
              disabled={isExecuting}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white flex items-center gap-1.5 shadow"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Run Full Round
            </button>

            <button
              onClick={handleReset}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700"
              title="Reset Persona Cycle"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* 6-Node Linear / Circular Stage Stepper */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {STAGES_LIST.map((stg, idx) => {
            const isCurrent = activeState.currentStage === stg;
            const isPassed = STAGES_LIST.indexOf(activeState.currentStage) > idx;

            return (
              <div
                key={stg}
                className={`p-3.5 rounded-xl border transition-all text-xs space-y-2 relative overflow-hidden ${
                  isCurrent
                    ? `${STAGE_ACCENT[stg]} ring-1 ring-cyan-500/50 shadow-lg`
                    : isPassed
                    ? "bg-slate-950/60 border-slate-800/80 opacity-80"
                    : "bg-slate-950/30 border-slate-800/40 opacity-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] text-slate-500">#{idx + 1}</span>
                  {STAGE_ICON[stg]}
                </div>
                <div className="font-bold text-slate-100 uppercase font-mono">{stg}</div>
                <div className="text-[10px] text-slate-400 leading-tight line-clamp-2">
                  {stg === 'dream' && 'Define vision & recall memory context'}
                  {stg === 'hope' && 'Architect solution & capture decisions'}
                  {stg === 'care' && 'Audit concurrency, safety & quality'}
                  {stg === 'joy' && 'Package, test & deploy release bundle'}
                  {stg === 'trust' && 'Verify doctor checks & boundaries'}
                  {stg === 'growth' && 'Consolidate memory & advance round'}
                </div>

                {isCurrent && (
                  <div className="w-full bg-cyan-400/20 h-1 rounded-full overflow-hidden mt-1">
                    <div className="bg-cyan-400 h-full w-full animate-pulse" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Generated Stage Artifacts History */}
        <div className="space-y-3 pt-2">
          <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-2">
            <FileCode2 className="w-4 h-4 text-purple-400" />
            Generated Stage Artifacts ({activeState.history.length})
          </h4>

          <div className="space-y-2 max-h-56 overflow-y-auto pr-1 font-mono text-xs">
            {activeState.history.map((art, i) => (
              <div
                key={i}
                className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-purple-950 text-purple-300 border border-purple-800/40 font-bold">
                      {art.stage}
                    </span>
                    <span className="font-semibold text-slate-200 truncate">{art.title}</span>
                  </div>
                  <div className="text-[11px] text-slate-400 font-sans mt-1">
                    {art.content}
                  </div>
                </div>

                <div className="text-[10px] text-slate-500 flex-shrink-0 font-mono">
                  {new Date(art.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
