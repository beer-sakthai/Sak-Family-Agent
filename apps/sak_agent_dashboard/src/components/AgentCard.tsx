"use client";

import React, { useState } from "react";
import {
  Cpu,
  Zap,
  Activity,
  Award,
  Shield,
  Eye,
  Terminal,
  Clock,
  Play,
  Send,
  CheckCircle2,
  AlertCircle,
  X,
  Loader2,
} from "lucide-react";
import { AgentPersona } from "@/lib/types";

interface AgentCardProps {
  agent: AgentPersona;
}

const personaIcons: Record<string, React.ReactNode> = {
  SakThai: <Terminal className="h-5 w-5 text-cyan-400" />,
  SakKing: <Zap className="h-5 w-5 text-purple-400" />,
  SakSee: <Eye className="h-5 w-5 text-amber-400" />,
  SakSit: <Shield className="h-5 w-5 text-emerald-400" />,
  SakJules: <Activity className="h-5 w-5 text-rose-400" />,
  SakTan: <Cpu className="h-5 w-5 text-indigo-400" />,
};

const personaGlows: Record<string, string> = {
  SakThai: "border-cyan-500/30 hover:border-cyan-500/60 shadow-cyan-950/40",
  SakKing: "border-purple-500/30 hover:border-purple-500/60 shadow-purple-950/40",
  SakSee: "border-amber-500/30 hover:border-amber-500/60 shadow-amber-950/40",
  SakSit: "border-emerald-500/30 hover:border-emerald-500/60 shadow-emerald-950/40",
  SakJules: "border-rose-500/30 hover:border-rose-500/60 shadow-rose-950/40",
  SakTan: "border-indigo-500/30 hover:border-indigo-500/60 shadow-indigo-950/40",
  Unattributed: "border-slate-600/40 hover:border-slate-500/60 shadow-slate-950/40",
};

const DEFAULT_PRESETS: Record<string, string[]> = {
  SakThai: [
    "Run cycle health check and tool guardrail audit",
    "Analyze memory store knowledge graph",
  ],
  SakJules: [
    "Run automated CI/CD gate and test battery",
    "Verify repo package parity and drift",
  ],
  SakKing: [
    "Generate executive product and monetization brief",
    "Prioritize active conductor roadmap tracks",
  ],
  SakSee: [
    "Review media assets and aesthetic UI themes",
    "Audit marketing conversion funnel copy",
  ],
  SakSit: [
    "Ingest technical documentation and index vector RAG",
    "Evaluate dataset schema and benchmark cards",
  ],
  SakTan: [
    "Record daily session memories and standup digest",
    "Sync personal voice notes to Telegram bridge",
  ],
};

export function AgentCard({ agent }: AgentCardProps) {
  const [isDispatchOpen, setIsDispatchOpen] = useState(false);
  const [taskInput, setTaskInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dispatchResult, setDispatchResult] = useState<{
    success: boolean;
    dispatchId?: string;
    message?: string;
    error?: string;
  } | null>(null);

  const isOnline = agent.status === "Active" || agent.status === "Ready";
  const glowClass = personaGlows[agent.name] || "border-slate-800 hover:border-slate-700";
  const icon = personaIcons[agent.name] || <Cpu className="h-5 w-5 text-cyan-400" />;

  const score = agent.benchmarkScore;
  const hasScore = typeof score === "number" && Number.isFinite(score);
  const presets = DEFAULT_PRESETS[agent.name] || [
    "Execute system telemetry scan",
    "Verify tool permissions",
  ];

  const handleDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskInput.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setDispatchResult(null);

    try {
      const res = await fetch("/api/dispatch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          persona: agent.name,
          task: taskInput.trim(),
        }),
      });
      const data = await res.json();

      if (res.ok && data.success) {
        setDispatchResult({
          success: true,
          dispatchId: data.dispatchId,
          message: data.message || `Dispatched to ${agent.name}`,
        });
        setTaskInput("");
      } else {
        setDispatchResult({
          success: false,
          error: data.error || "Dispatch request failed",
        });
      }
    } catch (err) {
      setDispatchResult({
        success: false,
        error: err instanceof Error ? err.message : "Network error during dispatch",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className={`glass-card p-5 rounded-2xl bg-slate-900/80 border backdrop-blur-xl shadow-xl transition-all duration-300 flex flex-col justify-between space-y-4 relative overflow-hidden group ${glowClass}`}
    >
      {/* Background ambient glow */}
      <div className="absolute -top-10 -right-10 w-32 h-32 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition-all duration-500 pointer-events-none" />

      {/* Card Header: Persona Icon, Name & Status Pulse */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-slate-800/80 border border-slate-700/50">
              {icon}
            </div>
            <div>
              <h4 className="text-lg font-bold font-display text-white tracking-tight flex items-center gap-2">
                {agent.name}
                {agent.badge && (
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/50">
                    {agent.badge}
                  </span>
                )}
              </h4>
              <p className="text-xs text-slate-400 line-clamp-2 mt-0.5 leading-snug">
                {agent.role}
              </p>
            </div>
          </div>

          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold font-mono border ${
              isOnline
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : agent.status === "Warning" || agent.status === "Alert"
                ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                : "bg-slate-800/80 text-slate-400 border-slate-700"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isOnline
                  ? "bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]"
                  : agent.status === "Warning" || agent.status === "Alert"
                  ? "bg-amber-400 animate-pulse"
                  : "bg-slate-500"
              }`}
            />
            {agent.status}
          </span>
        </div>

        {/* Model Badge */}
        <div className="mt-3 flex items-center gap-2">
          <span className="text-[11px] font-mono text-slate-300 px-2.5 py-1 rounded-md bg-slate-800/90 border border-slate-700/60 inline-flex items-center gap-1.5">
            <Cpu className="h-3 w-3 text-cyan-400" />
            {agent.model}
          </span>
        </div>
      </div>

      {/* Metrics Row: Latency & Total Runs */}
      <div className="grid grid-cols-2 gap-2 py-2 px-3 rounded-xl bg-slate-950/60 border border-slate-800/80 font-mono text-xs">
        <div>
          <span className="text-[10px] uppercase text-slate-400 block mb-0.5 flex items-center gap-1">
            <Clock className="h-3 w-3 text-cyan-400" /> Latency
          </span>
          <span className="font-bold text-cyan-300">{agent.latencyMs}ms</span>
        </div>
        <div>
          <span className="text-[10px] uppercase text-slate-400 block mb-0.5 flex items-center gap-1">
            <Activity className="h-3 w-3 text-emerald-400" /> Executions
          </span>
          <span className="font-bold text-emerald-300">{agent.runs} runs</span>
        </div>
      </div>

      {/* Benchmark Score Progress Bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-slate-400 text-[11px] flex items-center gap-1">
            <Award className="h-3 w-3 text-amber-400" /> Benchmark Score
          </span>
          {hasScore ? (
            <span className="font-bold text-emerald-400">{score!.toFixed(1)}%</span>
          ) : (
            <span className="text-slate-500" title="No benchmark recorded for this persona">
              not measured
            </span>
          )}
        </div>
        <div className="h-2 w-full bg-slate-800/90 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
          {hasScore ? (
            <div
              className="h-full bg-gradient-to-r from-cyan-500 via-teal-400 to-emerald-400 rounded-full transition-all duration-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]"
              style={{ width: `${Math.min(100, Math.max(0, score!))}%` }}
            />
          ) : (
            <div className="h-full w-full rounded-full bg-[repeating-linear-gradient(45deg,rgba(100,116,139,0.25)_0_6px,transparent_6px_12px)]" />
          )}
        </div>
      </div>

      {/* Skills Tags */}
      {agent.skills && agent.skills.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {agent.skills.map((skill) => (
            <span
              key={skill}
              className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950/40 text-cyan-300 border border-cyan-800/30"
            >
              #{skill}
            </span>
          ))}
        </div>
      )}

      {/* Interactive Dispatch Trigger & Expandable Console */}
      <div className="pt-2 border-t border-slate-800/80">
        {!isDispatchOpen ? (
          <button
            type="button"
            onClick={() => setIsDispatchOpen(true)}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-gradient-to-r from-cyan-600/20 to-teal-600/20 hover:from-cyan-600/30 hover:to-teal-600/30 border border-cyan-500/30 text-cyan-300 text-xs font-semibold font-mono transition-all duration-200 shadow-sm"
          >
            <Play className="h-3.5 w-3.5 fill-cyan-400 text-cyan-400" />
            Dispatch {agent.name}
          </button>
        ) : (
          <div className="space-y-2.5 p-3 rounded-xl bg-slate-950/90 border border-cyan-500/40 animate-in fade-in slide-in-from-top-1 duration-200">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono font-semibold text-cyan-300 flex items-center gap-1.5">
                <Zap className="h-3.5 w-3.5 text-cyan-400" />
                Live Task Dispatch
              </span>
              <button
                type="button"
                onClick={() => {
                  setIsDispatchOpen(false);
                  setDispatchResult(null);
                }}
                className="text-slate-400 hover:text-slate-200 p-0.5 rounded"
                aria-label="Close dispatch console"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Quick Prompt Presets */}
            <div className="flex flex-wrap gap-1">
              {presets.map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setTaskInput(preset)}
                  className="text-[10px] font-mono text-left px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 hover:text-cyan-300 hover:border-cyan-800/60 transition-colors"
                >
                  {preset}
                </button>
              ))}
            </div>

            {/* Task Form */}
            <form onSubmit={handleDispatch} className="space-y-2">
              <textarea
                value={taskInput}
                onChange={(e) => setTaskInput(e.target.value)}
                placeholder={`Instruct ${agent.name}...`}
                rows={2}
                disabled={isSubmitting}
                className="w-full text-xs bg-slate-900 border border-slate-700/80 rounded-lg p-2 text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 font-mono resize-none"
              />

              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] font-mono text-slate-500">
                  Streams to SSE Bus
                </span>
                <button
                  type="submit"
                  aria-label="Submit task dispatch"
                  disabled={!taskInput.trim() || isSubmitting}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white text-xs font-mono font-medium transition-all"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin" /> Dispatching...
                    </>
                  ) : (
                    <>
                      <Send className="h-3 w-3" /> Run Task
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Dispatch Receipt Feedback */}
            {dispatchResult && (
              <div
                className={`p-2 rounded-lg text-[11px] font-mono flex items-start gap-1.5 border ${
                  dispatchResult.success
                    ? "bg-emerald-950/40 text-emerald-300 border-emerald-800/50"
                    : "bg-rose-950/40 text-rose-300 border-rose-800/50"
                }`}
              >
                {dispatchResult.success ? (
                  <>
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold">{dispatchResult.message}</span>
                      {dispatchResult.dispatchId && (
                        <span className="block text-[10px] text-emerald-400/80">
                          Receipt ID: {dispatchResult.dispatchId}
                        </span>
                      )}
                    </div>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-3.5 w-3.5 text-rose-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold">Error:</span> {dispatchResult.error}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentCard;
