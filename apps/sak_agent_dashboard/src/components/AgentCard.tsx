"use client";

import React from "react";
import { Activity, Award, Brain, Clock, Cpu, Eye, Shield, Sparkles, Terminal, Zap } from "lucide-react";

import type { PersonaSummary } from "@/lib/contracts.generated";

interface AgentCardProps {
  agent: PersonaSummary;
}

/** Keyed by the canonical lowercase persona name, all six of them. */
const personaIcons: Record<string, React.ReactNode> = {
  sakthai: <Terminal className="h-5 w-5 text-cyan-400" />,
  sakking: <Zap className="h-5 w-5 text-purple-400" />,
  saksee: <Eye className="h-5 w-5 text-amber-400" />,
  saksit: <Shield className="h-5 w-5 text-emerald-400" />,
  sakjules: <Activity className="h-5 w-5 text-rose-400" />,
  saktan: <Sparkles className="h-5 w-5 text-sky-400" />,
};

const personaGlows: Record<string, string> = {
  sakthai: "border-cyan-500/30 hover:border-cyan-500/60 shadow-cyan-950/40",
  sakking: "border-purple-500/30 hover:border-purple-500/60 shadow-purple-950/40",
  saksee: "border-amber-500/30 hover:border-amber-500/60 shadow-amber-950/40",
  saksit: "border-emerald-500/30 hover:border-emerald-500/60 shadow-emerald-950/40",
  sakjules: "border-rose-500/30 hover:border-rose-500/60 shadow-rose-950/40",
  saktan: "border-sky-500/30 hover:border-sky-500/60 shadow-sky-950/40",
};

const DAY_SECONDS = 86_400;

type Status = "Active" | "Ready" | "Idle";

/**
 * Status derived from what we actually recorded, not asserted.
 *
 * A persona with no runs and no memory shard has genuinely never been used —
 * "Idle" is the truthful label, and the card renders it rather than being
 * hidden or given a plausible-looking "Ready".
 */
function deriveStatus(agent: PersonaSummary): Status {
  if (agent.runs === 0 && !agent.has_shard) return "Idle";
  if (agent.last_run_at !== null && Date.now() / 1000 - agent.last_run_at < DAY_SECONDS) {
    return "Active";
  }
  return "Ready";
}

export function AgentCard({ agent }: AgentCardProps) {
  const status = deriveStatus(agent);
  const glowClass = personaGlows[agent.name] ?? "border-slate-800 hover:border-slate-700";
  const icon = personaIcons[agent.name] ?? <Cpu className="h-5 w-5 text-cyan-400" />;

  // Real, derived from recorded runs and errors -- not the `?? 92.5` default
  // and `Math.random()` fallback this replaces. Undefined with no runs, and
  // shown as such.
  const successRate = agent.runs > 0 ? ((agent.runs - agent.errors) / agent.runs) * 100 : null;

  return (
    <div
      className={`glass-card p-5 rounded-2xl bg-slate-900/80 border backdrop-blur-xl shadow-xl transition-all duration-300 flex flex-col justify-between space-y-4 relative overflow-hidden group ${glowClass} ${
        status === "Idle" ? "opacity-70" : ""
      }`}
      data-testid={`agent-card-${agent.name}`}
    >
      <div className="absolute -top-10 -right-10 w-32 h-32 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition-all duration-500 pointer-events-none" />

      <div>
        {/* items-start: the text column is three lines tall, so centring the
            icon and the status pill against it leaves the name floating alone
            above both. */}
        <div className="mb-3 flex items-start justify-between gap-2">
          {/* The name owns the first line alone. Sharing it with the provider
              badge meant the two competed for the same shrinking row, and the
              name — the one thing that identifies the card — is what a
              `truncate` gave up first. min-w-0 on every level so the card can
              still narrow to whatever column the auto-fill grid gives it. */}
          <div className="flex min-w-0 flex-1 items-start space-x-2.5">
            <div className="p-2 rounded-xl bg-slate-800/80 border border-slate-700/50 shrink-0">
              {icon}
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="truncate text-lg font-bold font-display text-white tracking-tight">
                {agent.display_name}
              </h4>
              <p className="mt-1 flex flex-wrap items-center gap-x-1.5 gap-y-1 font-mono text-xs leading-snug text-slate-400">
                {agent.provider && (
                  <span className="rounded bg-cyan-950 px-1.5 py-0.5 text-[10px] text-cyan-400 border border-cyan-800/50">
                    {agent.provider}
                  </span>
                )}
                <span className="min-w-0">
                  {agent.has_shard
                    ? `${agent.fact_count} facts · ${agent.observation_count} observations`
                    : "no memory shard yet"}
                </span>
              </p>
            </div>
          </div>

          <span
            className={`inline-flex shrink-0 items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold font-mono border ${
              status === "Active"
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : status === "Ready"
                  ? "bg-slate-800/80 text-slate-300 border-slate-700"
                  : "bg-slate-900/80 text-slate-500 border-slate-800"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                status === "Active"
                  ? "bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]"
                  : status === "Ready"
                    ? "bg-slate-400"
                    : "bg-slate-600"
              }`}
            />
            {status}
          </span>
        </div>

        <div className="mt-3 flex items-center gap-2">
          <span className="text-[11px] font-mono text-slate-300 px-2.5 py-1 rounded-md bg-slate-800/90 border border-slate-700/60 inline-flex items-center gap-1.5 max-w-full">
            <Cpu className="h-3 w-3 text-cyan-400 shrink-0" />
            <span className="truncate">{agent.model || "no configured model"}</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 py-2 px-3 rounded-xl bg-slate-950/60 border border-slate-800/80 font-mono text-xs">
        <div>
          <span className="text-[10px] uppercase text-slate-400 mb-0.5 flex items-center gap-1">
            <Clock className="h-3 w-3 text-cyan-400" /> Avg latency
          </span>
          <span className="font-bold text-cyan-300">
            {agent.runs > 0 ? `${Math.round(agent.avg_latency_ms)}ms` : "—"}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase text-slate-400 mb-0.5 flex items-center gap-1">
            <Activity className="h-3 w-3 text-emerald-400" /> Executions
          </span>
          <span className="font-bold text-emerald-300">
            {agent.runs} {agent.runs === 1 ? "run" : "runs"}
          </span>
        </div>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-slate-400 text-[11px] flex items-center gap-1">
            <Award className="h-3 w-3 text-amber-400" /> Success rate
          </span>
          <span className="font-bold text-emerald-400">
            {successRate === null ? "no runs yet" : `${successRate.toFixed(1)}%`}
          </span>
        </div>
        <div className="h-2 w-full bg-slate-800/90 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 via-teal-400 to-emerald-400 rounded-full transition-all duration-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]"
            style={{ width: `${successRate ?? 0}%` }}
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 pt-1 font-mono text-[10px]">
        <span className="px-2 py-0.5 rounded-full bg-cyan-950/40 text-cyan-300 border border-cyan-800/30 inline-flex items-center gap-1">
          <Brain className="h-2.5 w-2.5" />
          {(agent.input_tokens + agent.output_tokens).toLocaleString()} tokens
        </span>
        {agent.errors > 0 && (
          <span className="px-2 py-0.5 rounded-full bg-rose-950/40 text-rose-300 border border-rose-800/30">
            {agent.errors} {agent.errors === 1 ? "error" : "errors"}
          </span>
        )}
      </div>
    </div>
  );
}

export default AgentCard;
