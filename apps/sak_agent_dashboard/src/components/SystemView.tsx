"use client";

import React, { useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowRight,
  Boxes,
  Brain,
  ChevronRight,
  Cpu,
  Crown,
  Database,
  FlaskConical,
  GitBranch,
  Plug,
  ShieldCheck,
  Terminal,
  Users,
  Wrench,
  type LucideIcon,
} from "lucide-react";

import { compactNumber } from "@/lib/format";
import { displayName } from "@/lib/persona";
import {
  SYSTEM_SNAPSHOT,
  linesOf,
  systemTotals,
  type CliNode,
  type SystemSnapshot,
} from "@/lib/system";

const PANEL =
  "rounded-2xl border border-line/80 bg-panel/70 p-pad backdrop-blur-xl";

function PanelHeader({
  icon: Icon,
  title,
  hint,
  accent,
  children,
}: {
  icon: LucideIcon;
  title: string;
  hint: string;
  accent: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        <h3 className="flex items-center gap-2 font-display text-base font-semibold text-fg">
          <Icon className={`h-4 w-4 ${accent}`} aria-hidden />
          {title}
        </h3>
        <p className="mt-0.5 text-xs text-fg-4">{hint}</p>
      </div>
      {children}
    </div>
  );
}

// --- KPI tiles ---------------------------------------------------------------

interface Stat {
  label: string;
  value: string;
  hint: string;
  icon: LucideIcon;
  accent: string;
}

function StatTiles({ snapshot }: { snapshot: SystemSnapshot }) {
  const t = systemTotals(snapshot);
  const lead = snapshot.personas.find((p) => p.lead);
  const floor = snapshot.tests.coverage_floor;
  const stats: Stat[] = [
    {
      label: "Personas",
      value: String(t.personas),
      hint: lead ? `${displayName(lead.name)} leads` : "no lead set",
      icon: Users,
      accent: "text-hue-cyan",
    },
    {
      label: "Skills",
      value: compactNumber(t.personaSkills + t.sharedSkills + t.librarySkills),
      hint: `${t.personaSkills} persona · ${t.sharedSkills} shared · ${t.librarySkills} library`,
      icon: Brain,
      accent: "text-hue-violet",
    },
    {
      label: "Built-in tools",
      value: String(t.tools),
      hint: t.mcpOnlyTools ? `${t.mcpOnlyTools} MCP-only` : "all in the agent loop",
      icon: Wrench,
      accent: "text-hue-emerald",
    },
    {
      label: "CLI commands",
      value: String(t.cliCommands),
      hint: `${snapshot.cli.commands?.length ?? 0} top-level`,
      icon: Terminal,
      accent: "text-hue-sky",
    },
    {
      label: "CI workflows",
      value: String(t.workflows),
      hint: `${t.prWorkflows} run on pull requests`,
      icon: GitBranch,
      accent: "text-hue-amber",
    },
    {
      label: "Tests",
      value: compactNumber(t.testFunctions),
      hint: floor !== null ? `test functions · ${floor}% coverage floor` : "test functions",
      icon: FlaskConical,
      accent: "text-hue-rose",
    },
  ];

  return (
    <ul
      aria-label="System at a glance"
      className="grid grid-cols-2 gap-gap sm:grid-cols-3 xl:grid-cols-6"
    >
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <li
            key={stat.label}
            className="rounded-2xl border border-line/80 bg-panel/70 p-4 backdrop-blur-xl"
          >
            <p className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-fg-4">
              <Icon className={`h-3 w-3 ${stat.accent}`} aria-hidden />
              {stat.label}
            </p>
            <p className="mt-1.5 font-display text-2xl font-bold tracking-tight text-fg">
              {stat.value}
            </p>
            <p className="mt-0.5 truncate font-mono text-[11px] text-fg-4" title={stat.hint}>
              {stat.hint}
            </p>
          </li>
        );
      })}
    </ul>
  );
}

// --- Architecture ------------------------------------------------------------

interface Layer {
  title: string;
  detail: string;
  icon: LucideIcon;
  accent: string;
  /** Package entries whose line counts this layer sums. */
  modules: string[];
}

const LAYERS: Layer[] = [
  {
    title: "Entry points",
    detail: "CLI · chat REPL · MCP stdio · web API",
    icon: Terminal,
    accent: "text-hue-sky",
    modules: ["cli", "mcp", "web"],
  },
  {
    title: "Agent loop",
    detail: "providers, context filter, eval log",
    icon: Cpu,
    accent: "text-hue-cyan",
    modules: ["agent"],
  },
  {
    title: "Guardrails",
    detail: "pre/post checks on every tool call",
    icon: ShieldCheck,
    accent: "text-hue-rose",
    modules: [],
  },
  {
    title: "Tool registry",
    detail: "BUILTIN_TOOLS + external MCP servers",
    icon: Wrench,
    accent: "text-hue-emerald",
    modules: [],
  },
  {
    title: "MemoryStore",
    detail: "facts, observations, sync, family view",
    icon: Brain,
    accent: "text-hue-violet",
    modules: ["memory"],
  },
  {
    title: "SQLite",
    detail: "memory.db per persona shard",
    icon: Database,
    accent: "text-hue-amber",
    modules: [],
  },
];

function ArchitectureFlow({ snapshot }: { snapshot: SystemSnapshot }) {
  return (
    <section aria-labelledby="system-architecture" className={PANEL}>
      <PanelHeader
        icon={Boxes}
        title="Architecture"
        hint="A strictly layered package — each layer has one job. Every tool call passes the guardrails."
        accent="text-hue-cyan"
      />
      <h4 id="system-architecture" className="sr-only">
        Request flow through the package
      </h4>
      <ol className="flex flex-col items-stretch gap-2 lg:flex-row lg:items-center">
        {LAYERS.map((layer, index) => {
          const Icon = layer.icon;
          const lines = layer.modules.reduce((sum, name) => sum + linesOf(snapshot, name), 0);
          return (
            <li key={layer.title} className="flex flex-col items-center gap-2 lg:flex-1 lg:flex-row">
              <div className="w-full rounded-xl border border-line bg-raised/40 p-3 transition-colors hover:border-line-strong">
                <p className="flex items-center gap-2 text-sm font-semibold text-fg">
                  <Icon className={`h-4 w-4 shrink-0 ${layer.accent}`} aria-hidden />
                  {layer.title}
                </p>
                <p className="mt-1 text-[11px] leading-snug text-fg-4">{layer.detail}</p>
                {lines > 0 && (
                  <p className="mt-1.5 font-mono text-[10px] text-fg-5">
                    {compactNumber(lines)} lines
                  </p>
                )}
              </div>
              {index < LAYERS.length - 1 && (
                <>
                  <ArrowDown className="h-4 w-4 shrink-0 text-fg-5 lg:hidden" aria-hidden />
                  <ArrowRight className="hidden h-4 w-4 shrink-0 text-fg-5 lg:block" aria-hidden />
                </>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}

// --- Personas ----------------------------------------------------------------

function PersonaGrid({ snapshot }: { snapshot: SystemSnapshot }) {
  const maxSkills = Math.max(1, ...snapshot.personas.map((p) => p.skill_count));
  return (
    <section aria-labelledby="system-personas" className={PANEL}>
      <PanelHeader
        icon={Users}
        title="The family"
        hint="Each persona's role, default model and own skill overlay, read from personas/<name>/config."
        accent="text-hue-violet"
      />
      <h4 id="system-personas" className="sr-only">
        Personas
      </h4>
      <ul className="grid gap-gap sm:grid-cols-2 xl:grid-cols-3">
        {snapshot.personas.map((persona) => (
          <li
            key={persona.name}
            className={`relative overflow-hidden rounded-xl border bg-raised/30 p-4 ${
              persona.lead ? "border-accent/50" : "border-line"
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="flex items-center gap-1.5 font-display text-base font-semibold text-fg">
                  {displayName(persona.name)}
                  {persona.lead && (
                    <span className="inline-flex items-center gap-1 rounded-full border border-accent/40 bg-accent/10 px-1.5 py-0.5 text-[10px] font-medium text-accent">
                      <Crown className="h-3 w-3" aria-hidden />
                      Lead
                    </span>
                  )}
                </p>
                <p className="mt-0.5 text-xs text-fg-3">{persona.role || "—"}</p>
              </div>
              <span
                className="shrink-0 rounded-md border border-line bg-sunken/60 px-1.5 py-0.5 font-mono text-[10px] text-fg-3"
                title={`${persona.provider ?? "default"} / ${persona.model ?? "default"}`}
              >
                {persona.provider ?? "default"}
              </span>
            </div>

            <p className="mt-2 line-clamp-2 text-[11px] leading-snug text-fg-4" title={persona.domain}>
              {persona.domain}
            </p>

            <p className="mt-3 truncate font-mono text-[11px] text-fg-2" title={persona.model ?? ""}>
              {persona.model ?? "provider default"}
            </p>

            <div className="mt-3">
              <div className="flex items-baseline justify-between text-[11px]">
                <span className="text-fg-4">Skills</span>
                <span className="font-mono text-fg-2">{persona.skill_count}</span>
              </div>
              <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-sunken" aria-hidden>
                <div
                  className="h-full rounded-full bg-accent"
                  style={{ width: `${(persona.skill_count / maxSkills) * 100}%` }}
                />
              </div>
            </div>

            <p className="mt-3 flex items-center gap-1.5 text-[11px] text-fg-4">
              <Plug className="h-3 w-3 shrink-0" aria-hidden />
              <span className="shrink-0 whitespace-nowrap">
                {persona.mcp_servers.length === 0
                  ? "No MCP servers"
                  : `${persona.mcp_servers.length} MCP server${persona.mcp_servers.length === 1 ? "" : "s"}`}
              </span>
              {persona.mcp_servers.length > 0 && (
                <span className="min-w-0 truncate font-mono text-fg-5" title={persona.mcp_servers.join(", ")}>
                  · {persona.mcp_servers.join(", ")}
                </span>
              )}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}

// --- Ranked bar list (package subsystems, test trees) -------------------------

interface BarRow {
  label: string;
  value: number;
  /** Shown after the value, e.g. "12 files". */
  note?: string;
}

/**
 * A ranked, single-measure bar list. One hue (the accent), no legend — the
 * panel title names the measure — and every value printed as text in ink, so
 * the list doubles as its own table view.
 */
function BarList({ rows, unit }: { rows: BarRow[]; unit: string }) {
  const sorted = [...rows].sort((a, b) => b.value - a.value || a.label.localeCompare(b.label));
  const max = Math.max(1, ...sorted.map((r) => r.value));
  return (
    <ol className="space-y-1.5">
      {sorted.map((row) => (
        <li
          key={row.label}
          className="grid grid-cols-[minmax(0,9rem)_1fr_auto] items-center gap-3 rounded-md px-1 py-0.5 text-xs hover:bg-raised/40"
          title={`${row.label}: ${row.value.toLocaleString()} ${unit}${row.note ? ` · ${row.note}` : ""}`}
        >
          <span className="truncate font-mono text-fg-2">{row.label}</span>
          <span className="h-2 overflow-hidden rounded-full bg-sunken" aria-hidden>
            <span
              className="block h-full rounded-full bg-accent"
              style={{ width: `${Math.max(2, (row.value / max) * 100)}%` }}
            />
          </span>
          <span className="text-right font-mono tabular-nums text-fg-3">
            {row.value.toLocaleString()}
            {row.note && <span className="ml-1.5 text-fg-5">{row.note}</span>}
          </span>
        </li>
      ))}
    </ol>
  );
}

function PackagePanel({ snapshot }: { snapshot: SystemSnapshot }) {
  const total = snapshot.package.reduce((sum, m) => sum + m.lines, 0);
  return (
    <section aria-labelledby="system-package" className={PANEL}>
      <PanelHeader
        icon={Boxes}
        title="Package subsystems"
        hint={`personas/sakthai/sakthai — ${total.toLocaleString()} lines of Python, by subsystem`}
        accent="text-hue-sky"
      />
      <h4 id="system-package" className="sr-only">
        Lines of code per subsystem
      </h4>
      <BarList
        unit="lines"
        rows={snapshot.package.map((m) => ({
          label: m.name,
          value: m.lines,
          note: m.kind === "package" ? `${m.files}f` : undefined,
        }))}
      />
    </section>
  );
}

// --- Tools -------------------------------------------------------------------

function ToolsPanel({ snapshot }: { snapshot: SystemSnapshot }) {
  return (
    <section aria-labelledby="system-tools" className={PANEL}>
      <PanelHeader
        icon={Wrench}
        title="Built-in tools"
        hint="One registry serves both the agent loop and the MCP server."
        accent="text-hue-emerald"
      />
      <h4 id="system-tools" className="sr-only">
        Built-in tools
      </h4>
      <ul className="grid gap-2 sm:grid-cols-2">
        {snapshot.tools.map((tool) => (
          <li key={tool.name} className="rounded-lg border border-line bg-raised/30 px-3 py-2">
            <p className="flex items-center gap-2">
              <code className="truncate font-mono text-xs text-fg">{tool.name}</code>
              {tool.mcp_only && (
                <span className="shrink-0 rounded border border-hue-amber-line bg-hue-amber-tint px-1 text-[10px] text-hue-amber">
                  MCP only
                </span>
              )}
            </p>
            <p className="mt-0.5 line-clamp-2 text-[11px] leading-snug text-fg-4" title={tool.summary}>
              {tool.summary}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}

// --- CLI tree ----------------------------------------------------------------

function CliBranch({ node, path }: { node: CliNode; path: string }) {
  const full = `${path} ${node.name}`;
  if (!node.commands || node.commands.length === 0) {
    return (
      <li className="flex items-baseline gap-2 py-0.5">
        <code className="shrink-0 font-mono text-xs text-fg-2">{node.name}</code>
        <span className="min-w-0 truncate text-[11px] text-fg-5" title={node.help}>
          {node.help}
        </span>
      </li>
    );
  }
  return (
    <li className="py-0.5">
      <details className="group">
        <summary className="flex cursor-pointer list-none items-baseline gap-2 rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">
          <ChevronRight
            className="h-3 w-3 shrink-0 translate-y-0.5 text-fg-4 transition-transform group-open:rotate-90"
            aria-hidden
          />
          <code className="shrink-0 font-mono text-xs text-fg">{node.name}</code>
          <span className="rounded bg-sunken px-1 font-mono text-[10px] text-fg-4">
            {node.commands.length}
          </span>
          <span className="min-w-0 truncate text-[11px] text-fg-5" title={node.help}>
            {node.help}
          </span>
        </summary>
        <ul className="ml-4 border-l border-line-soft pl-3" aria-label={`${full.trim()} subcommands`}>
          {node.commands.map((child) => (
            <CliBranch key={child.name} node={child} path={full} />
          ))}
        </ul>
      </details>
    </li>
  );
}

function CliPanel({ snapshot }: { snapshot: SystemSnapshot }) {
  return (
    <section aria-labelledby="system-cli" className={PANEL}>
      <PanelHeader
        icon={Terminal}
        title="CLI"
        hint="Every command under `sakthai`, read from the click tree. Groups expand."
        accent="text-hue-sky"
      />
      <h4 id="system-cli" className="sr-only">
        CLI command tree
      </h4>
      <ul className="max-h-[28rem] overflow-y-auto pr-1">
        {(snapshot.cli.commands ?? []).map((node) => (
          <CliBranch key={node.name} node={node} path="sakthai" />
        ))}
      </ul>
    </section>
  );
}

// --- CI workflows ------------------------------------------------------------

type WorkflowFilter = "pr" | "all";

function WorkflowsPanel({ snapshot }: { snapshot: SystemSnapshot }) {
  const [filter, setFilter] = useState<WorkflowFilter>("pr");
  const shown = useMemo(
    () => snapshot.workflows.filter((w) => filter === "all" || w.gates_prs),
    [snapshot.workflows, filter],
  );
  const options: { id: WorkflowFilter; label: string }[] = [
    { id: "pr", label: "Runs on PRs" },
    { id: "all", label: `All ${snapshot.workflows.length}` },
  ];

  return (
    <section aria-labelledby="system-workflows" className={PANEL}>
      <PanelHeader
        icon={GitBranch}
        title="CI workflows"
        hint=".github/workflows — triggers and jobs"
        accent="text-hue-amber"
      >
        <div role="group" aria-label="Filter workflows" className="flex rounded-lg border border-line p-0.5">
          {options.map((option) => (
            <button
              key={option.id}
              type="button"
              aria-pressed={filter === option.id}
              onClick={() => setFilter(option.id)}
              className={`rounded-md px-2 py-1 text-[11px] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                filter === option.id ? "bg-raised text-fg" : "text-fg-4 hover:text-fg-2"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </PanelHeader>
      <h4 id="system-workflows" className="sr-only">
        Workflows
      </h4>
      <ul className="max-h-[28rem] space-y-1.5 overflow-y-auto pr-1">
        {shown.map((workflow) => (
          <li key={workflow.file} className="rounded-lg border border-line bg-raised/30 px-3 py-2">
            <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
              <p className="min-w-0 truncate text-xs font-medium text-fg" title={workflow.name}>
                {workflow.name}
              </p>
              <code className="font-mono text-[10px] text-fg-5">{workflow.file}</code>
            </div>
            <div className="mt-1.5 flex flex-wrap gap-1">
              {workflow.triggers.map((trigger) => (
                <span
                  key={trigger}
                  className="rounded border border-line bg-sunken/60 px-1 font-mono text-[10px] text-fg-3"
                >
                  {trigger}
                </span>
              ))}
              <span className="font-mono text-[10px] text-fg-5">
                · {workflow.jobs.length} job{workflow.jobs.length === 1 ? "" : "s"}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

// --- Tests & skills ------------------------------------------------------------

function TestsPanel({ snapshot }: { snapshot: SystemSnapshot }) {
  const { tests } = snapshot;
  return (
    <section aria-labelledby="system-tests" className={PANEL}>
      <PanelHeader
        icon={FlaskConical}
        title="Test trees"
        hint={
          tests.coverage_floor !== null
            ? `Test files per tree. The sakthai package is held to ${tests.coverage_floor}% branch coverage in ci.yml.`
            : "Test files per tree."
        }
        accent="text-hue-rose"
      />
      <h4 id="system-tests" className="sr-only">
        Test files per tree
      </h4>
      <BarList
        unit="test files"
        rows={tests.trees.map((tree) => ({ label: tree.name, value: tree.files, note: tree.runner }))}
      />
    </section>
  );
}

function SkillsPanel({ snapshot }: { snapshot: SystemSnapshot }) {
  return (
    <section aria-labelledby="system-skills" className={PANEL}>
      <PanelHeader
        icon={Brain}
        title="Shared & library skills"
        hint="Sak- skills every persona shares, and the curated library/ by category."
        accent="text-hue-violet"
      />
      <h4 id="system-skills" className="sr-only">
        Shared and library skills
      </h4>
      <div className="flex flex-wrap gap-1.5">
        {snapshot.skills.shared.map((name) => (
          <code
            key={name}
            className="rounded-md border border-accent/30 bg-accent/10 px-1.5 py-0.5 font-mono text-[11px] text-fg-2"
          >
            {name}
          </code>
        ))}
      </div>
      <div className="mt-4">
        <BarList
          unit="skills"
          rows={snapshot.skills.library_categories.map((c) => ({ label: c.name, value: c.skills }))}
        />
      </div>
    </section>
  );
}

// --- The view --------------------------------------------------------------------

function snapshotLabel(meta: SystemSnapshot["meta"]): string {
  const date = meta.source_date ? new Date(meta.source_date) : null;
  const when =
    date && !Number.isNaN(date.getTime())
      ? date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
      : null;
  if (meta.source_commit && when) return `commit ${meta.source_commit} · ${when}`;
  if (meta.source_commit) return `commit ${meta.source_commit}`;
  return "unknown commit";
}

export default function SystemView({ snapshot = SYSTEM_SNAPSHOT }: { snapshot?: SystemSnapshot }) {
  return (
    <div className="space-y-gap" data-testid="system-view">
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-hue-emerald-line bg-hue-emerald-tint/40 px-4 py-2.5 text-xs">
        <p className="text-fg-2">
          <span className="font-semibold text-hue-emerald">Real data.</span> A snapshot of this
          repository — not the sample runtime data the other sections show when no agent is
          connected.
        </p>
        <p className="font-mono text-[11px] text-fg-4" title={`Generated by ${snapshot.meta.generator}`}>
          {snapshotLabel(snapshot.meta)}
        </p>
      </div>

      <StatTiles snapshot={snapshot} />
      <ArchitectureFlow snapshot={snapshot} />
      <PersonaGrid snapshot={snapshot} />

      <div className="grid grid-cols-1 gap-gap xl:grid-cols-2">
        <PackagePanel snapshot={snapshot} />
        <ToolsPanel snapshot={snapshot} />
      </div>
      <div className="grid grid-cols-1 gap-gap xl:grid-cols-2">
        <CliPanel snapshot={snapshot} />
        <WorkflowsPanel snapshot={snapshot} />
      </div>
      <div className="grid grid-cols-1 gap-gap xl:grid-cols-2">
        <TestsPanel snapshot={snapshot} />
        <SkillsPanel snapshot={snapshot} />
      </div>
    </div>
  );
}
