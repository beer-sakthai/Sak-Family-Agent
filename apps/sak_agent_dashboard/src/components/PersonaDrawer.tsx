"use client";

import React from "react";
import {
  Activity,
  AlertTriangle,
  Award,
  Brain,
  Clock,
  Cpu,
  Database,
  Filter,
  MessageSquare,
} from "lucide-react";

import type { PersonaSummary } from "@/lib/contracts.generated";
import { compactNumber, duration, relativeTime } from "@/lib/format";
import type { TabId } from "@/lib/nav";

import { Drawer } from "./Drawer";

interface PersonaDrawerProps {
  persona: PersonaSummary;
  /** Every persona, so each figure can be stated as a share of the family. */
  family: readonly PersonaSummary[];
  /** Whether this persona is currently in the global filter. */
  filtered: boolean;
  onToggleFilter: () => void;
  /** Jump to a panel already narrowed to this persona. */
  onNavigate: (tab: TabId) => void;
  onClose: () => void;
}

/**
 * A single figure, with the share of the family it accounts for.
 *
 * The share is the point of the drawer. "1,204 runs" on a card says nothing
 * about whether that is most of the family's work or a rounding error next to
 * SakThai; the bar answers that without a second panel to cross-reference.
 */
function ShareRow({
  label,
  icon: Icon,
  value,
  share,
  accent,
  bar,
}: {
  label: string;
  icon: typeof Activity;
  value: string;
  /** 0..1, or null where the family total is zero and a share is undefined. */
  share: number | null;
  /** Both class names are spelled out: Tailwind scans source text, so a
      `text-` swapped to `bg-` at runtime would never be generated. */
  accent: string;
  bar: string;
}) {
  const percent = share === null ? null : Math.round(share * 100);

  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between gap-3">
        <span className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wider text-fg-4">
          <Icon className={`h-3 w-3 ${accent}`} aria-hidden />
          {label}
        </span>
        <span className="font-display text-sm font-bold text-fg">{value}</span>
      </div>
      <div className="flex items-center gap-2">
        <div
          className="h-1.5 flex-1 overflow-hidden rounded-full bg-raised/90"
          role="presentation"
        >
          <div
            className={`h-full rounded-full ${bar} transition-[width] duration-500`}
            style={{ width: `${percent ?? 0}%` }}
          />
        </div>
        <span className="w-20 shrink-0 text-right font-mono text-[10px] text-fg-4">
          {percent === null ? "no family total" : `${percent}% of family`}
        </span>
      </div>
    </div>
  );
}

/** `part / whole`, or null where the whole is zero — never NaN on screen. */
function share(part: number, whole: number): number | null {
  return whole > 0 ? part / whole : null;
}

/**
 * The per-persona detail surface, opened from a card on the Overview.
 *
 * The card had nowhere left to grow: it already carries the name, the model,
 * latency, runs, success rate and tokens, and every further figure made it
 * denser rather than more useful. The drawer takes the figures that need
 * context — how much of the family's work this persona actually does — and
 * gives them the room to be stated as shares rather than as bare counts.
 *
 * It reads nothing the Overview did not already have. There is no extra fetch
 * behind it, so opening one cannot show a persona a different refresh from the
 * card behind it.
 */
export function PersonaDrawer({
  persona,
  family,
  filtered,
  onToggleFilter,
  onNavigate,
  onClose,
}: PersonaDrawerProps) {
  const totals = family.reduce(
    (acc, item) => ({
      runs: acc.runs + item.runs,
      errors: acc.errors + item.errors,
      tokens: acc.tokens + item.input_tokens + item.output_tokens,
      facts: acc.facts + item.fact_count,
      observations: acc.observations + item.observation_count,
    }),
    { runs: 0, errors: 0, tokens: 0, facts: 0, observations: 0 },
  );

  const tokens = persona.input_tokens + persona.output_tokens;
  const successRate = persona.runs > 0 ? ((persona.runs - persona.errors) / persona.runs) * 100 : null;

  return (
    <Drawer
      title={persona.display_name}
      subtitle={
        <span className="font-mono">
          {persona.name}
          {persona.last_run_at !== null && ` · last run ${relativeTime(persona.last_run_at * 1000)}`}
        </span>
      }
      icon={<Cpu className="h-5 w-5 text-accent" aria-hidden />}
      onClose={onClose}
      data-testid="persona-drawer"
    >
      <div className="space-y-6">
        <section className="grid grid-cols-2 gap-2 font-mono text-xs">
          <div className="rounded-xl border border-line/80 bg-sunken/60 p-3">
            <span className="mb-1 block text-[10px] uppercase tracking-wider text-fg-4">
              Provider
            </span>
            <span className="block truncate text-fg-2">{persona.provider || "unset"}</span>
          </div>
          <div className="rounded-xl border border-line/80 bg-sunken/60 p-3">
            <span className="mb-1 block text-[10px] uppercase tracking-wider text-fg-4">Model</span>
            <span className="block truncate text-fg-2" title={persona.model || undefined}>
              {persona.model || "unset"}
            </span>
          </div>
          <div className="rounded-xl border border-line/80 bg-sunken/60 p-3">
            <span className="mb-1 block text-[10px] uppercase tracking-wider text-fg-4">
              Avg latency
            </span>
            <span className="block text-hue-cyan">
              {persona.runs > 0 ? duration(persona.avg_latency_ms) : "—"}
            </span>
          </div>
          <div className="rounded-xl border border-line/80 bg-sunken/60 p-3">
            <span className="mb-1 block text-[10px] uppercase tracking-wider text-fg-4">
              Success rate
            </span>
            <span className="block text-hue-emerald">
              {successRate === null ? "no runs yet" : `${successRate.toFixed(1)}%`}
            </span>
          </div>
        </section>

        <section className="space-y-4" aria-label="Share of family totals">
          <h3 className="font-display text-sm font-bold text-fg-2">Share of the family</h3>
          <ShareRow
            label="Runs"
            icon={Activity}
            value={persona.runs.toLocaleString()}
            share={share(persona.runs, totals.runs)}
            accent="text-hue-emerald"
            bar="bg-hue-emerald"
          />
          <ShareRow
            label="Errors"
            icon={AlertTriangle}
            value={persona.errors.toLocaleString()}
            share={share(persona.errors, totals.errors)}
            accent="text-hue-rose"
            bar="bg-hue-rose"
          />
          <ShareRow
            label="Tokens"
            icon={Brain}
            value={compactNumber(tokens)}
            share={share(tokens, totals.tokens)}
            accent="text-hue-violet"
            bar="bg-hue-violet"
          />
          <ShareRow
            label="Facts"
            icon={Database}
            value={persona.fact_count.toLocaleString()}
            share={share(persona.fact_count, totals.facts)}
            accent="text-hue-cyan"
            bar="bg-hue-cyan"
          />
          <ShareRow
            label="Observations"
            icon={Award}
            value={persona.observation_count.toLocaleString()}
            share={share(persona.observation_count, totals.observations)}
            accent="text-hue-amber"
            bar="bg-hue-amber"
          />
        </section>

        <section className="space-y-2">
          <h3 className="font-display text-sm font-bold text-fg-2">Memory shard</h3>
          <p className="font-mono text-xs leading-relaxed text-fg-3">
            {persona.has_shard ? (
              <>
                <code className="text-fg-2">~/.sakthai/{persona.name}/memory.db</code> holds{" "}
                {persona.fact_count.toLocaleString()} facts and{" "}
                {persona.observation_count.toLocaleString()} observations.
              </>
            ) : (
              <>
                No shard yet. One is created at{" "}
                <code className="text-fg-2">~/.sakthai/{persona.name}/memory.db</code> on this
                persona&rsquo;s first memory write.
              </>
            )}
          </p>
        </section>

        <section className="flex flex-wrap gap-2 border-t border-line-soft pt-4">
          <button
            type="button"
            onClick={onToggleFilter}
            aria-pressed={filtered}
            className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 font-mono text-xs transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
              filtered
                ? "border-accent/50 bg-accent/10 text-accent"
                : "border-line-strong bg-raised/80 text-fg-2 hover:bg-raised-2"
            }`}
          >
            <Filter className="h-3 w-3" aria-hidden />
            {filtered ? "In the filter" : "Filter to this persona"}
          </button>
          <button
            type="button"
            onClick={() => onNavigate("sessions")}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line-strong bg-raised/80 px-3 py-1.5 font-mono text-xs text-fg-2 transition-colors hover:bg-raised-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <MessageSquare className="h-3 w-3" aria-hidden />
            Sessions
          </button>
          <button
            type="button"
            onClick={() => onNavigate("memory")}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line-strong bg-raised/80 px-3 py-1.5 font-mono text-xs text-fg-2 transition-colors hover:bg-raised-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <Database className="h-3 w-3" aria-hidden />
            Memory
          </button>
          <button
            type="button"
            onClick={() => onNavigate("analytics")}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line-strong bg-raised/80 px-3 py-1.5 font-mono text-xs text-fg-2 transition-colors hover:bg-raised-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <Clock className="h-3 w-3" aria-hidden />
            Analytics
          </button>
        </section>
      </div>
    </Drawer>
  );
}

export default PersonaDrawer;
