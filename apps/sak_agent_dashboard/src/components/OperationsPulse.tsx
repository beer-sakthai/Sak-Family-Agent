"use client";

import React from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  CircleDashed,
  Gauge,
  GitBranch,
  ShieldAlert,
  type LucideIcon,
} from "lucide-react";

import type {
  AuditPayload,
  MetricsPayload,
  PersonasPayload,
  WorkflowsPayload,
} from "@/lib/contracts.generated";
import type { TabId } from "@/lib/nav";

interface OperationsPulseProps {
  metrics: MetricsPayload | null;
  personas: PersonasPayload | null;
  audit: AuditPayload | null;
  workflows: WorkflowsPayload | null;
  /** Opens the source panel for a summary card when the shell owns navigation. */
  onNavigate?: (tab: TabId) => void;
}

type SignalTone = "healthy" | "attention" | "neutral";

interface Signal {
  label: string;
  value: string;
  detail: string;
  tone: SignalTone;
  icon: LucideIcon;
  tab: TabId;
  progress: number | null;
}

const TONE_STYLES: Record<
  SignalTone,
  { panel: string; text: string; line: string; fill: string; label: string; icon: LucideIcon }
> = {
  healthy: {
    panel: "border-hue-emerald-line/50 bg-hue-emerald-tint/20",
    text: "text-hue-emerald",
    line: "bg-hue-emerald",
    fill: "bg-hue-emerald",
    label: "Healthy",
    icon: CheckCircle2,
  },
  attention: {
    panel: "border-hue-amber-line/50 bg-hue-amber-tint/20",
    text: "text-hue-amber",
    line: "bg-hue-amber",
    fill: "bg-hue-amber",
    label: "Needs attention",
    icon: AlertTriangle,
  },
  neutral: {
    panel: "border-line bg-raised/25",
    text: "text-fg-3",
    line: "bg-fg-4",
    fill: "bg-fg-4",
    label: "Awaiting data",
    icon: CircleDashed,
  },
};

function clampProgress(value: number | null): number | null {
  if (value === null || !Number.isFinite(value)) return null;
  return Math.max(0, Math.min(100, value));
}

function SignalCard({ signal, onNavigate }: { signal: Signal; onNavigate?: (tab: TabId) => void }) {
  const style = TONE_STYLES[signal.tone];
  const StatusIcon = style.icon;
  const Icon = signal.icon;
  const interactive = Boolean(onNavigate);
  const Root = interactive ? "button" : "div";

  return (
    <Root
      {...(interactive
        ? {
            type: "button" as const,
            onClick: () => onNavigate?.(signal.tab),
            "aria-label": `${signal.label}: ${signal.value}. ${signal.detail}. Open ${signal.label} details.`,
          }
        : {})}
      className={`group relative overflow-hidden rounded-2xl border p-4 text-left transition-all ${style.panel} ${
        interactive
          ? "cursor-pointer hover:-translate-y-0.5 hover:border-accent/60 hover:shadow-lg hover:shadow-accent/5 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          : ""
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-[0.16em] text-fg-4">
            <Icon className={`h-3.5 w-3.5 ${style.text}`} aria-hidden />
            {signal.label}
          </p>
          <p className="mt-2 font-display text-2xl font-bold tracking-tight text-fg">{signal.value}</p>
          <p className="mt-1 min-h-8 text-xs leading-4 text-fg-3">{signal.detail}</p>
        </div>
        <span
          className={`inline-flex shrink-0 items-center gap-1 rounded-full border border-current/20 bg-panel/40 px-2 py-1 font-mono text-[10px] ${style.text}`}
        >
          <StatusIcon className="h-3 w-3" aria-hidden />
          <span className="hidden 2xl:inline">{style.label}</span>
        </span>
      </div>
      <div className="mt-4 h-1 overflow-hidden rounded-full bg-panel/70" aria-hidden>
        <div
          className={`h-full rounded-full transition-[width] duration-500 ${style.fill}`}
          style={{ width: `${signal.progress ?? 0}%` }}
        />
      </div>
      {interactive && (
        <span className="absolute bottom-4 right-4 font-mono text-[10px] text-fg-5 opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100">
          Open →
        </span>
      )}
    </Root>
  );
}

/**
 * A compact cross-source operational briefing.
 *
 * Dashboard panels retain their detailed charts and tables. This strip answers
 * the first triage questions from the same returned payloads — whether the
 * family is available, healthy, safe, and completing work — and each card
 * opens the panel that can explain its figure. No status is invented: an
 * absent payload is visibly an "Awaiting data" signal rather than green.
 */
export function OperationsPulse({ metrics, personas, audit, workflows, onNavigate }: OperationsPulseProps) {
  const knownPersonas = personas?.personas ?? [];
  const readyPersonas = knownPersonas.filter((persona) => persona.runs > 0 || persona.has_shard).length;

  const successRate =
    metrics && metrics.total_runs > 0 ? Math.max(0, Math.min(100, (1 - metrics.error_rate) * 100)) : null;

  const criticalEvents = (audit?.severity_counts.critical ?? 0) + (audit?.severity_counts.high ?? 0);

  const runs = workflows?.runs ?? [];
  const failedRuns = runs.filter((run) => run.status === "failed").length;
  const completedRuns = runs.filter((run) => run.status === "completed").length;

  const signals: Signal[] = [
    {
      label: "Runtime coverage",
      value: personas ? `${readyPersonas} / ${knownPersonas.length}` : "—",
      detail: personas
        ? readyPersonas === knownPersonas.length
          ? "Every persona has a runtime footprint"
          : `${knownPersonas.length - readyPersonas} persona${knownPersonas.length - readyPersonas === 1 ? "" : "s"} idle or unconfigured`
        : "Waiting for persona inventory",
      tone: !personas ? "neutral" : readyPersonas === knownPersonas.length ? "healthy" : "attention",
      icon: Activity,
      tab: "overview",
      progress: personas && knownPersonas.length > 0 ? (readyPersonas / knownPersonas.length) * 100 : null,
    },
    {
      label: "Run quality",
      value: successRate === null ? "—" : `${successRate.toFixed(1)}%`,
      detail:
        successRate === null
          ? "No completed runs to evaluate"
          : metrics!.error_rate === 0
            ? "No recorded execution errors"
            : `${Math.round(metrics!.error_rate * metrics!.total_runs)} error${Math.round(metrics!.error_rate * metrics!.total_runs) === 1 ? "" : "s"} across ${metrics!.total_runs.toLocaleString()} runs`,
      tone: successRate === null ? "neutral" : successRate >= 98 ? "healthy" : "attention",
      icon: Gauge,
      tab: "analytics",
      progress: clampProgress(successRate),
    },
    {
      label: "Security queue",
      value: audit ? criticalEvents.toLocaleString() : "—",
      detail: !audit
        ? "Waiting for the guardrail event feed"
        : criticalEvents === 0
          ? "No high or critical events recorded"
          : `${criticalEvents} high or critical event${criticalEvents === 1 ? "" : "s"} require review`,
      tone: !audit ? "neutral" : criticalEvents === 0 ? "healthy" : "attention",
      icon: ShieldAlert,
      tab: "audit",
      progress: audit ? (criticalEvents === 0 ? 100 : Math.max(5, 100 - criticalEvents * 20)) : null,
    },
    {
      label: "Workflow health",
      value: workflows ? `${completedRuns} / ${runs.length}` : "—",
      detail: !workflows
        ? "Waiting for workflow history"
        : runs.length === 0
          ? "No workflow runs recorded yet"
          : failedRuns === 0
            ? "No failed workflow runs in this window"
            : `${failedRuns} failed workflow run${failedRuns === 1 ? "" : "s"} requires review`,
      tone:
        !workflows || runs.length === 0
          ? "neutral"
          : failedRuns === 0
            ? "healthy"
            : "attention",
      icon: GitBranch,
      tab: "workflows",
      progress: workflows && runs.length > 0 ? (completedRuns / runs.length) * 100 : null,
    },
  ];

  return (
    <section
      aria-labelledby="operations-pulse-title"
      data-testid="operations-pulse"
      className="glass-panel rounded-2xl border border-line/80 bg-panel/60 p-4 backdrop-blur-xl sm:p-5"
    >
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-accent">Operations</p>
          <h2 id="operations-pulse-title" className="mt-1 font-display text-base font-bold tracking-tight text-fg">
            System pulse
          </h2>
        </div>
        <p className="max-w-xl text-xs leading-5 text-fg-4">
          A live briefing across runtime, execution, security, and workflow signals. Select a card for detail.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {signals.map((signal) => (
          <SignalCard key={signal.label} signal={signal} onNavigate={onNavigate} />
        ))}
      </div>
    </section>
  );
}

export default OperationsPulse;
