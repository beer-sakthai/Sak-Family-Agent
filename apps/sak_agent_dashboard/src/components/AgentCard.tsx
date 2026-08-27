"use client";

import React from "react";
import { Activity, Award, Brain, Clock, Cpu, Eye, Shield, Sparkles, Terminal, Zap } from "lucide-react";

import type { PersonaSummary } from "@/lib/contracts.generated";

interface AgentCardProps {
  agent: PersonaSummary;
  /** Excluded by the persona filter: still rendered, but pushed back. */
  dimmed?: boolean;
  /** Included by the persona filter. */
  selected?: boolean;
  /** When given, the card becomes a toggle for the global persona filter. */
  onToggle?: () => void;
}

/** Keyed by the canonical lowercase persona name, all six of them. */
const personaIcons: Record<string, React.ReactNode> = {
  sakthai: <Terminal className="h-5 w-5 text-hue-cyan" />,
  sakking: <Zap className="h-5 w-5 text-hue-purple" />,
  saksee: <Eye className="h-5 w-5 text-hue-amber" />,
  saksit: <Shield className="h-5 w-5 text-hue-emerald" />,
  sakjules: <Activity className="h-5 w-5 text-hue-rose" />,
  saktan: <Sparkles className="h-5 w-5 text-hue-sky" />,
};

const personaGlows: Record<string, string> = {
  sakthai: "border-hue-cyan-line/30 hover:border-hue-cyan-line/60 shadow-hue-cyan-tint/40",
  sakking: "border-hue-purple-line/30 hover:border-hue-purple-line/60 shadow-hue-purple-tint/40",
  saksee: "border-hue-amber-line/30 hover:border-hue-amber-line/60 shadow-hue-amber-tint/40",
  saksit: "border-hue-emerald-line/30 hover:border-hue-emerald-line/60 shadow-hue-emerald-tint/40",
  sakjules: "border-hue-rose-line/30 hover:border-hue-rose-line/60 shadow-hue-rose-tint/40",
  saktan: "border-hue-sky-line/30 hover:border-hue-sky-line/60 shadow-hue-sky-tint/40",
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

export function AgentCard({ agent, dimmed = false, selected = false, onToggle }: AgentCardProps) {
  const status = deriveStatus(agent);
  const glowClass = personaGlows[agent.name] ?? "border-line hover:border-line-strong";
  const icon = personaIcons[agent.name] ?? <Cpu className="h-5 w-5 text-hue-cyan" />;

  // Real, derived from recorded runs and errors -- not the `?? 92.5` default
  // and `Math.random()` fallback this replaces. Undefined with no runs, and
  // shown as such.
  const successRate = agent.runs > 0 ? ((agent.runs - agent.errors) / agent.runs) * 100 : null;

  // Interactive cards are <button>s so they are reachable by keyboard and
  // announced as pressable; a plain card stays a <div> rather than becoming a
  // button that does nothing.
  const Root = onToggle ? "button" : "div";
  const interactive = onToggle
    ? {
        type: "button" as const,
        onClick: onToggle,
        "aria-pressed": selected,
        "aria-label": `${selected ? "Remove" : "Add"} ${agent.display_name} ${selected ? "from" : "to"} the persona filter`,
      }
    : {};

  return (
    <Root
      {...interactive}
      className={`glass-card p-5 rounded-2xl bg-panel/80 border backdrop-blur-xl shadow-xl transition-all duration-300 flex flex-col justify-between space-y-4 relative overflow-hidden group text-left w-full focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${glowClass} ${
        status === "Idle" ? "opacity-70" : ""
      } ${dimmed ? "opacity-40 saturate-50" : ""} ${
        selected ? "ring-2 ring-accent ring-offset-2 ring-offset-canvas" : ""
      }`}
      data-testid={`agent-card-${agent.name}`}
    >
      <div className="absolute -top-10 -right-10 w-32 h-32 bg-hue-cyan/5 rounded-full blur-2xl group-hover:bg-hue-cyan/10 transition-all duration-500 pointer-events-none" />

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
            <div className="p-2 rounded-xl bg-raised/80 border border-line-strong/50 shrink-0">
              {icon}
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="truncate text-lg font-bold font-display text-fg tracking-tight">
                {agent.display_name}
              </h4>
              <p className="mt-1 flex flex-wrap items-center gap-x-1.5 gap-y-1 font-mono text-xs leading-snug text-fg-3">
                {agent.provider && (
                  <span className="rounded bg-hue-cyan-tint px-1.5 py-0.5 text-[10px] text-hue-cyan border border-hue-cyan-line/50">
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
                ? "bg-hue-emerald/10 text-hue-emerald border-hue-emerald-line/30"
                : status === "Ready"
                  ? "bg-raised/80 text-fg-2 border-line-strong"
                  : "bg-panel/80 text-fg-4 border-line"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                status === "Active"
                  ? "bg-hue-emerald animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]"
                  : status === "Ready"
                    ? "bg-fg-3"
                    : "bg-fg-5"
              }`}
            />
            {status}
          </span>
        </div>

        <div className="mt-3 flex items-center gap-2">
          <span className="text-[11px] font-mono text-fg-2 px-2.5 py-1 rounded-md bg-raised/90 border border-line-strong/60 inline-flex items-center gap-1.5 max-w-full">
            <Cpu className="h-3 w-3 text-hue-cyan shrink-0" />
            <span className="truncate">{agent.model || "no configured model"}</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 py-2 px-3 rounded-xl bg-sunken/60 border border-line/80 font-mono text-xs">
        <div>
          <span className="text-[10px] uppercase text-fg-3 mb-0.5 flex items-center gap-1">
            <Clock className="h-3 w-3 text-hue-cyan" /> Avg latency
          </span>
          <span className="font-bold text-hue-cyan">
            {agent.runs > 0 ? `${Math.round(agent.avg_latency_ms)}ms` : "—"}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase text-fg-3 mb-0.5 flex items-center gap-1">
            <Activity className="h-3 w-3 text-hue-emerald" /> Executions
          </span>
          <span className="font-bold text-hue-emerald">
            {agent.runs} {agent.runs === 1 ? "run" : "runs"}
          </span>
        </div>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-fg-3 text-[11px] flex items-center gap-1">
            <Award className="h-3 w-3 text-hue-amber" /> Success rate
          </span>
          <span className="font-bold text-hue-emerald">
            {successRate === null ? "no runs yet" : `${successRate.toFixed(1)}%`}
          </span>
        </div>
        <div className="h-2 w-full bg-raised/90 rounded-full overflow-hidden p-0.5 border border-line-strong/50">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 via-teal-400 to-emerald-400 rounded-full transition-all duration-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]"
            style={{ width: `${successRate ?? 0}%` }}
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 pt-1 font-mono text-[10px]">
        <span className="px-2 py-0.5 rounded-full bg-hue-cyan-tint/40 text-hue-cyan border border-hue-cyan-line/30 inline-flex items-center gap-1">
          <Brain className="h-2.5 w-2.5" />
          {(agent.input_tokens + agent.output_tokens).toLocaleString()} tokens
        </span>
        {agent.errors > 0 && (
          <span className="px-2 py-0.5 rounded-full bg-hue-rose-tint/40 text-hue-rose border border-hue-rose-line/30">
            {agent.errors} {agent.errors === 1 ? "error" : "errors"}
          </span>
        )}
      </div>
    </Root>
  );
}

export default AgentCard;
