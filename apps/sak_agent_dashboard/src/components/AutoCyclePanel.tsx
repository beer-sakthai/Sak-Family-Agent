"use client";

import React, { useState } from "react";
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
  XCircle,
} from "lucide-react";
import { AutoCycleData, CycleStage } from "@/lib/types";

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

function StageCard({ stage }: { stage: CycleStage }) {
  return (
    <div
      className={`p-4 rounded-2xl bg-slate-900/80 border backdrop-blur-xl ${
        STAGE_ACCENT[stage.stage] ?? "border-slate-800/80"
      }`}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[11px] font-mono text-slate-500">
          {String(stage.number).padStart(2, "0")}
        </span>
        {STAGE_ICON[stage.stage]}
        <h5 className="text-sm font-bold font-display text-white tracking-tight uppercase">
          {stage.stage}
        </h5>
      </div>
      <p className="text-[11.5px] text-slate-200 font-medium leading-relaxed">
        {stage.goal}
      </p>
      <p className="text-[11px] text-slate-400 leading-relaxed mt-1">
        {stage.guidance}
      </p>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {stage.commands.map((c) => (
          <code
            key={c}
            className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-cyan-300 border border-slate-700/60"
          >
            sakthai {c}
          </code>
        ))}
      </div>
    </div>
  );
}

export function AutoCyclePanel({ data }: AutoCyclePanelProps) {
  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <RefreshCw className="h-5 w-5 text-cyan-400" />
            Sak Family Auto-Cycle
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Loading auto-cycle definition…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
          <RefreshCw className="h-5 w-5 text-cyan-400" />
          {data.overview.title}
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60">
            {data.personas.length} personas
          </span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
            ≤{data.roundCap} rounds each
          </span>
        </h3>
        <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
          {data.overview.description}
        </p>
        <div className="mt-1.5 flex flex-wrap gap-3 text-[10.5px] font-mono text-slate-500">
          <span>spec: <code className="text-cyan-300">{data.overview.specPath}</code></span>
          <span>skill: <code className="text-cyan-300">{data.overview.skillPath}</code></span>
        </div>
      </div>

      {/* SAFETY RULE — most important thing on the page */}
      <div className="glass-panel rounded-2xl border-2 border-rose-500/50 bg-rose-500/[0.07] backdrop-blur-xl overflow-hidden shadow-lg shadow-rose-950/30">
        <div className="p-5 border-b border-rose-500/25">
          <h4 className="text-base font-bold font-display text-white tracking-tight flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-rose-400" />
            {data.safetyRule.headline}
          </h4>
          <p className="text-[11.5px] text-slate-200 mt-2 leading-relaxed max-w-3xl">
            {data.safetyRule.body}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-rose-500/20">
          <div className="p-5">
            <h5 className="text-[10px] font-mono uppercase tracking-wider text-emerald-300 flex items-center gap-1.5 mb-2">
              <Check className="h-3 w-3" />
              Counts as live authorization
            </h5>
            <ul className="space-y-1 text-[11px] font-mono text-slate-300">
              {data.safetyRule.liveAuthorizationPhrases.map((p) => (
                <li key={p} className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">✓</span>
                  <span>{p}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="p-5">
            <h5 className="text-[10px] font-mono uppercase tracking-wider text-rose-300 flex items-center gap-1.5 mb-2">
              <XCircle className="h-3 w-3" />
              Does NOT count, however urgent
            </h5>
            <ul className="space-y-1 text-[11px] font-mono text-slate-300">
              {data.safetyRule.nonAuthorizationPhrases.map((p) => (
                <li key={p} className="flex items-start gap-2">
                  <span className="text-rose-400 mt-0.5">✕</span>
                  <span>{p}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="px-5 pb-4">
          <div className="rounded-lg border border-slate-800/80 bg-slate-950/80 overflow-hidden">
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800/80 bg-slate-900/70">
              <span className="text-[10px] font-mono text-emerald-300 uppercase flex items-center gap-1.5">
                <FlaskConical className="h-3 w-3" />
                safe default (test mode)
              </span>
              <CopyButton payload={data.safetyRule.testCommand} />
            </div>
            <pre className="p-3 text-[11px] font-mono text-cyan-300 overflow-x-auto leading-relaxed">
              {data.safetyRule.testCommand}
            </pre>
          </div>
        </div>

        <div className="px-5 pb-5">
          <p className="text-[11px] text-slate-400 leading-relaxed border-l-2 border-rose-500/40 pl-3">
            <span className="text-rose-300 font-bold">Why this rule exists: </span>
            {data.safetyRule.baselineEvidence}
          </p>
        </div>
      </div>

      {/* Stages */}
      <div>
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <RefreshCw className="h-4 w-4 text-cyan-400" />
          The six stages
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.stages.map((s) => (
            <StageCard key={s.stage} stage={s} />
          ))}
        </div>
        <p className="text-[11px] text-slate-500 mt-2 font-mono">
          Growth wraps back to Dream — that wrap is what the loop skill automates,
          up to {data.roundCap} rounds per invocation.
        </p>
      </div>

      {/* Personas */}
      <div>
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-2">
          <Users className="h-4 w-4 text-emerald-400" />
          Per-persona dispatch
        </h4>
        <p className="text-[11px] text-slate-400 mb-3 max-w-3xl leading-relaxed">
          The homes below are <span className="text-rose-300 font-bold">live paths</span> —
          used only after explicit live authorization. A test dispatch uses a
          fresh <code className="text-cyan-300">mktemp -d</code> per persona instead.
        </p>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 overflow-hidden">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-4 py-2.5">Persona</th>
                <th className="px-4 py-2.5">Live SAKTHAI_HOME</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {data.personas.map((p) => (
                <tr key={p.persona} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-3 font-bold text-white">
                    <span className="inline-flex items-center gap-1.5">
                      {p.lead && <Crown className="h-3 w-3 text-amber-400" />}
                      {p.persona}
                      {p.lead && (
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                          lead
                        </span>
                      )}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-rose-300">{p.liveHome}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Skills */}
      <div>
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Layers className="h-4 w-4 text-purple-400" />
          The two composing skills
        </h4>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {data.skills.map((s) => (
            <div
              key={s.name}
              className={`p-4 rounded-2xl bg-slate-900/80 border backdrop-blur-xl ${
                s.layer === "claude-code"
                  ? "border-cyan-500/40"
                  : "border-emerald-500/40"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <code className="text-[12.5px] font-mono text-white font-bold">
                  {s.name}
                </code>
                <span
                  className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-full border ${
                    s.layer === "claude-code"
                      ? "bg-cyan-500/10 text-cyan-300 border-cyan-500/40"
                      : "bg-emerald-500/10 text-emerald-300 border-emerald-500/40"
                  }`}
                >
                  {s.layer}
                </span>
              </div>
              <div className="text-[10px] font-mono text-slate-500 mb-2 break-all">
                {s.path}
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed">{s.purpose}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Dispatch + errors + resolved gap */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h5 className="text-[11px] font-bold font-display text-white uppercase tracking-wide mb-2">
            One message, six subagents
          </h5>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            {data.dispatchNote}
          </p>
        </div>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h5 className="text-[11px] font-bold font-display text-white uppercase tracking-wide mb-2">
            Error handling
          </h5>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            {data.errorHandling}
          </p>
        </div>
        <div className="glass-panel rounded-2xl border border-emerald-500/30 bg-emerald-500/[0.04] backdrop-blur-xl p-5">
          <h5 className="text-[11px] font-bold font-display text-white uppercase tracking-wide mb-2 flex items-center gap-1.5">
            <Check className="h-3 w-3 text-emerald-400" />
            Resolved gap
          </h5>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            {data.resolvedGap}
          </p>
        </div>
      </div>

      {/* CLI */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Terminal className="h-4 w-4 text-emerald-400" />
          Driving the cycle by hand
        </h4>
        <ul className="space-y-1.5 font-mono text-[11px]">
          {data.cliCommands.map((c) => (
            <li key={c.command} className="flex items-start gap-3">
              <code className="text-cyan-300 whitespace-nowrap">{c.command}</code>
              <span className="text-slate-400">— {c.purpose}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default AutoCyclePanel;
