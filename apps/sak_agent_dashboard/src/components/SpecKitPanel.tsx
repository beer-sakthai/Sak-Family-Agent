"use client";

import React, { useState } from "react";
import {
  BookOpen,
  Check,
  ClipboardList,
  Copy,
  ExternalLink,
  FileCode,
  FlaskConical,
  GitBranch,
  Layers,
  Package,
  Puzzle,
  Route,
  ScrollText,
  Settings,
  ShieldAlert,
  ShieldCheck,
  Terminal,
  Workflow,
} from "lucide-react";
import { GithubIcon as Github } from "./GithubIcon";
import {
  SpecKitData,
  SpecKitTemplate,
  SpecKitUpstream,
  SpecKitWorkflowStep,
} from "@/lib/types";

interface SpecKitPanelProps {
  data: SpecKitData | null;
}

const STEP_ICONS: Record<string, React.ReactNode> = {
  specify: <ScrollText className="h-4 w-4 text-cyan-300" />,
  plan: <Route className="h-4 w-4 text-purple-300" />,
  tasks: <ClipboardList className="h-4 w-4 text-emerald-300" />,
  implement: <FileCode className="h-4 w-4 text-amber-300" />,
};

function SpecKitCopyButton({ payload }: { payload: string }) {
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

function UpstreamCard({ upstream }: { upstream: SpecKitUpstream }) {
  return (
    <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden">
      <div className="p-5 border-b border-slate-800/70 flex flex-col md:flex-row md:items-start md:justify-between gap-3">
        <div>
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-cyan-400" />
            Upstream — github/spec-kit
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60">
              {upstream.license}
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              Python {upstream.minPython}
            </span>
          </h4>
          <p className="text-[11px] text-slate-400 mt-1 max-w-3xl leading-relaxed">
            The tool this .specify/ install comes from. Templates and workflows
            below are populated from local disk; the roster here is what the
            upstream ships to any project — including commands you can opt into
            beyond what&apos;s currently wired.
          </p>
          <a
            href={upstream.repoUrl}
            target="_blank"
            rel="noreferrer noopener"
            className="mt-1.5 inline-flex items-center gap-1.5 text-[11px] font-mono text-cyan-300 hover:text-cyan-200"
          >
            <ExternalLink className="h-3 w-3" />
            {upstream.repoUrl.replace("https://", "")}
          </a>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-slate-800/70">
        <div className="p-5">
          <h5 className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
            <Package className="h-3 w-3 text-emerald-400" />
            Install
          </h5>
          <div className="rounded-lg border border-slate-800/80 bg-slate-950/80 overflow-hidden">
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800/80 bg-slate-900/70">
              <span className="text-[10px] font-mono text-slate-400 uppercase">
                shell
              </span>
              <SpecKitCopyButton payload={upstream.installCommand} />
            </div>
            <pre className="p-3 text-[11px] font-mono text-cyan-300 overflow-x-auto">
              {upstream.installCommand}
            </pre>
          </div>
          <div className="mt-3">
            <h5 className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1.5">
              Required tools
            </h5>
            <div className="flex flex-wrap gap-1.5">
              {upstream.requiredTools.map((t) => (
                <span
                  key={t}
                  className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/60"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="p-5 lg:col-span-2">
          <h5 className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
            Upstream slash commands
          </h5>
          <ul className="space-y-1.5 font-mono text-[11px]">
            {upstream.commands.map((c) => (
              <li
                key={c.slash}
                className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-950/60 border border-slate-800/80"
              >
                <code className="text-cyan-300 whitespace-nowrap">{c.slash}</code>
                <span className="text-slate-300 flex-1 leading-relaxed">
                  {c.purpose}
                </span>
                {c.optional && (
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-700/40 text-slate-300 border border-slate-600/40">
                    optional
                  </span>
                )}
              </li>
            ))}
          </ul>
          <div className="mt-3">
            <h5 className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1.5">
              Supported integrations
            </h5>
            <div className="flex flex-wrap gap-1.5">
              {upstream.supportedIntegrations.map((i) => (
                <span
                  key={i}
                  className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/40"
                >
                  {i}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
      <div className="px-5 pb-5 pt-2 border-t border-slate-800/70 bg-slate-950/40">
        <p className="text-[11px] text-slate-400 leading-relaxed">
          {upstream.layoutNote}
        </p>
      </div>
    </div>
  );
}

function StepIcon({ step }: { step: SpecKitWorkflowStep }) {
  if (step.kind === "gate") {
    return <ShieldAlert className="h-4 w-4 text-rose-300" />;
  }
  return STEP_ICONS[step.id] ?? <Workflow className="h-4 w-4 text-slate-300" />;
}

function EmptyState({ rootPath }: { rootPath: string }) {
  return (
    <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 p-10 text-center">
      <ShieldAlert className="h-6 w-6 text-amber-400 mx-auto mb-3" />
      <p className="text-sm text-slate-300 font-mono">
        No SpecKit installation detected.
      </p>
      <p className="text-[11px] text-slate-500 mt-1 font-mono">
        Looked in: <code className="text-cyan-300">{rootPath || "unknown"}</code>
      </p>
      <p className="text-xs text-slate-400 mt-4 max-w-lg mx-auto leading-relaxed">
        Initialize SpecKit at the repo root with{" "}
        <code className="text-cyan-300">speckit init</code> to enable the
        specify → plan → tasks → implement workflow, or set{" "}
        <code className="text-cyan-300">SPECKIT_DIR</code> to point at an
        existing installation.
      </p>
    </div>
  );
}

function TemplateCard({ template }: { template: SpecKitTemplate }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 overflow-hidden">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-900/50 transition-colors text-left"
      >
        <div className="flex items-center gap-2.5">
          <FileCode className="h-4 w-4 text-cyan-400" />
          <div>
            <code className="text-[12px] font-mono text-white font-semibold">
              {template.name}
            </code>
            <div className="text-[10.5px] font-mono text-slate-500 mt-0.5">
              {template.path}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 font-mono text-[10px] text-slate-400">
          <span className="px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700/60">
            {template.lines} lines
          </span>
          <span className="px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700/60">
            {template.bytes.toLocaleString()} B
          </span>
          <span className="text-slate-500">{expanded ? "▾" : "▸"}</span>
        </div>
      </button>
      {expanded && (
        <pre className="p-4 text-[11px] font-mono text-slate-300 bg-slate-950/80 border-t border-slate-800/80 overflow-x-auto whitespace-pre-wrap leading-relaxed">
          {template.preview}
          {template.lines > 12 && (
            <span className="text-slate-500">
              {"\n… "}
              ({template.lines - 12} more lines)
            </span>
          )}
        </pre>
      )}
    </div>
  );
}

export function SpecKitPanel({ data }: SpecKitPanelProps) {
  if (!data || !data.present) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Layers className="h-5 w-5 text-cyan-400" />
            SpecKit
          </h3>
          <p className="text-xs text-slate-400 mt-0.5 max-w-3xl leading-relaxed">
            Spec-driven-development workflow tooling for this repo.
          </p>
        </div>
        <EmptyState rootPath={data?.rootPath ?? ""} />
        {data?.upstream && <UpstreamCard upstream={data.upstream} />}
      </div>
    );
  }

  const totalTemplateLines = data.templates.reduce((s, t) => s + t.lines, 0);

  const speckitVersion =
    data.integrationState?.version ??
    data.initOptions?.speckitVersion ??
    "unknown";

  const constitutionStatus = data.constitution
    ? data.constitution.isTemplate
      ? {
          label: "Template",
          cls: "bg-amber-500/15 text-amber-300 border-amber-500/40",
          icon: <ShieldAlert className="h-3 w-3" />,
          note: "Placeholder tokens still present — run /speckit.constitution to populate.",
        }
      : {
          label: "Ratified",
          cls: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
          icon: <ShieldCheck className="h-3 w-3" />,
          note: "Placeholders replaced — project constitution is in effect.",
        }
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Layers className="h-5 w-5 text-cyan-400" />
            SpecKit
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60">
              v{speckitVersion}
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5 max-w-3xl leading-relaxed">
            Spec-driven-development workflow for this repo. Templates drive the
            specify → plan → tasks → implement cycle, with review gates between
            phases; each installed integration provides the concrete commands the
            workflow dispatches.
          </p>
          <p className="text-[10.5px] font-mono text-slate-500 mt-1">
            Root: <code className="text-cyan-300">{data.rootPath}</code>
          </p>
        </div>
      </div>

      {/* Upstream */}
      <UpstreamCard upstream={data.upstream} />

      {/* Stat tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Workflow className="h-3 w-3 text-cyan-400" />
            Workflows
          </div>
          <div className="text-3xl font-extrabold text-white font-display">
            {data.workflows.length}
          </div>
          <div className="text-[10px] font-mono text-slate-500">
            SDD cycles registered
          </div>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Puzzle className="h-3 w-3 text-emerald-400" />
            Integrations
          </div>
          <div className="text-3xl font-extrabold text-emerald-300 font-display">
            {data.integrations.length}
          </div>
          <div className="text-[10px] font-mono text-slate-500">
            {data.integrationState?.installedIntegrations.join(", ") || "none"}
          </div>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <FileCode className="h-3 w-3 text-amber-400" />
            Templates
          </div>
          <div className="text-3xl font-extrabold text-amber-300 font-display">
            {data.templates.length}
          </div>
          <div className="text-[10px] font-mono text-slate-500">
            {totalTemplateLines.toLocaleString()} lines total
          </div>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <BookOpen className="h-3 w-3 text-rose-400" />
            Constitution
          </div>
          {constitutionStatus ? (
            <div className="text-lg font-extrabold text-white font-display mt-1 flex items-center gap-2">
              <span
                className={`px-2 py-0.5 rounded-full border text-[11px] font-mono uppercase flex items-center gap-1 ${constitutionStatus.cls}`}
              >
                {constitutionStatus.icon}
                {constitutionStatus.label}
              </span>
            </div>
          ) : (
            <div className="text-lg font-extrabold text-slate-500 font-display mt-1">
              Not created
            </div>
          )}
          <div className="text-[10px] font-mono text-slate-500 mt-1">
            {data.constitution ? `${data.constitution.lines} lines` : "no constitution.md"}
          </div>
        </div>
      </div>

      {/* Config + Integration state */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
            <Settings className="h-4 w-4 text-cyan-400" />
            init-options.json
          </h4>
          {data.initOptions ? (
            <dl className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <dt className="text-slate-400">ai</dt>
              <dd className="text-white">{data.initOptions.ai}</dd>
              <dt className="text-slate-400">integration</dt>
              <dd className="text-white">{data.initOptions.integration}</dd>
              <dt className="text-slate-400">script</dt>
              <dd className="text-white">{data.initOptions.script}</dd>
              <dt className="text-slate-400">feature_numbering</dt>
              <dd className="text-white">{data.initOptions.featureNumbering}</dd>
              <dt className="text-slate-400">here</dt>
              <dd className="text-white">{String(data.initOptions.here)}</dd>
              <dt className="text-slate-400">speckit_version</dt>
              <dd className="text-white">{data.initOptions.speckitVersion}</dd>
            </dl>
          ) : (
            <p className="text-[11px] font-mono text-slate-500 italic">
              init-options.json not found.
            </p>
          )}
        </div>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
            <Puzzle className="h-4 w-4 text-emerald-400" />
            integration.json
          </h4>
          {data.integrationState ? (
            <div className="space-y-2 text-[11px] font-mono">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Current integration</span>
                <span className="text-emerald-300 font-bold">
                  {data.integrationState.currentIntegration}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Default</span>
                <span className="text-white">
                  {data.integrationState.defaultIntegration}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Schema</span>
                <span className="text-white">
                  v{data.integrationState.integrationStateSchema}
                </span>
              </div>
              <div className="pt-2 border-t border-slate-800/60">
                <div className="text-slate-400 text-[10px] uppercase mb-1.5">
                  Installed
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {data.integrationState.installedIntegrations.map((i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/40 text-[10px] uppercase"
                    >
                      {i}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-[11px] font-mono text-slate-500 italic">
              integration.json not found.
            </p>
          )}
        </div>
      </div>

      {/* Workflows */}
      <div className="space-y-4">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
          <Workflow className="h-4 w-4 text-cyan-400" />
          Workflows
        </h4>
        {data.workflows.length === 0 ? (
          <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 p-6 text-center text-[11px] font-mono text-slate-500 italic">
            No workflows registered.
          </div>
        ) : (
          data.workflows.map((wf) => (
            <div
              key={wf.id}
              className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden"
            >
              <div className="p-5 border-b border-slate-800/70">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h5 className="text-base font-bold font-display text-white tracking-tight">
                        {wf.name}
                      </h5>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
                        v{wf.version}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
                        id: {wf.id}
                      </span>
                    </div>
                    {wf.description && (
                      <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                        {wf.description}
                      </p>
                    )}
                    <div className="mt-1.5 flex flex-wrap gap-3 text-[10.5px] font-mono text-slate-500">
                      {wf.author && <span>author: {wf.author}</span>}
                      {wf.requiresSpeckitVersion && (
                        <span>requires speckit {wf.requiresSpeckitVersion}</span>
                      )}
                      {wf.installedAt && (
                        <span>installed: {wf.installedAt.slice(0, 10)}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Inputs */}
              {wf.inputs.length > 0 && (
                <div className="px-5 py-3 border-b border-slate-800/70 bg-slate-950/40">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
                    Inputs
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 font-mono text-[11px]">
                    {wf.inputs.map((inp) => (
                      <div
                        key={inp.name}
                        className="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800/70"
                      >
                        <div className="flex items-center justify-between">
                          <code className="text-cyan-300">{inp.name}</code>
                          <div className="flex items-center gap-1">
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
                              {inp.type}
                            </span>
                            {inp.required ? (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40 uppercase">
                                required
                              </span>
                            ) : (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/40 text-slate-300 border border-slate-600/40 uppercase">
                                optional
                              </span>
                            )}
                          </div>
                        </div>
                        {inp.prompt && (
                          <p className="text-[10.5px] text-slate-400 mt-1">
                            {inp.prompt}
                          </p>
                        )}
                        {inp.default && (
                          <p className="text-[10px] text-slate-500 mt-0.5">
                            default: <code className="text-cyan-300">{inp.default}</code>
                          </p>
                        )}
                        {inp.enum && inp.enum.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {inp.enum.map((e) => (
                              <span
                                key={e}
                                className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/60"
                              >
                                {e}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Steps timeline */}
              <div className="p-5">
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-3">
                  Steps
                </div>
                <ol className="space-y-2">
                  {wf.steps.map((step, idx) => (
                    <li
                      key={`${wf.id}-${step.id}-${idx}`}
                      className={`p-3 rounded-xl border flex items-start gap-3 ${
                        step.kind === "gate"
                          ? "bg-rose-500/[0.05] border-rose-500/30"
                          : "bg-slate-950/60 border-slate-800/80"
                      }`}
                    >
                      <div className="mt-0.5 p-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
                        <StepIcon step={step} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[11px] font-mono text-slate-500">
                            {String(idx + 1).padStart(2, "0")}
                          </span>
                          <code className="text-[12px] font-mono font-bold text-white">
                            {step.id}
                          </code>
                          {step.kind === "gate" ? (
                            <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40">
                              review gate
                            </span>
                          ) : step.command ? (
                            <code className="text-[10.5px] font-mono text-cyan-300 px-1.5 py-0.5 rounded bg-slate-800/70 border border-slate-700/60">
                              {step.command}
                            </code>
                          ) : null}
                          {step.integration && (
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/60">
                              via {step.integration.replace(/[{}\s]/g, "")}
                            </span>
                          )}
                        </div>
                        {step.message && (
                          <p className="text-[11px] text-slate-300 mt-1 leading-relaxed">
                            {step.message}
                          </p>
                        )}
                        {step.options && step.options.length > 0 && (
                          <div className="mt-1.5 flex flex-wrap gap-1">
                            {step.options.map((o) => (
                              <span
                                key={o}
                                className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                                  o === "approve"
                                    ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/40"
                                    : o === "reject"
                                    ? "bg-rose-500/10 text-rose-300 border-rose-500/40"
                                    : "bg-slate-800 text-slate-300 border-slate-700/60"
                                }`}
                              >
                                {o}
                              </span>
                            ))}
                            {step.onReject && (
                              <span className="text-[10px] font-mono text-slate-500 ml-1">
                                on reject: {step.onReject}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Integrations */}
      {data.integrations.length > 0 && (
        <div className="space-y-4">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Puzzle className="h-4 w-4 text-emerald-400" />
            Installed integrations
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.integrations.map((integ) => (
              <div
                key={integ.integration}
                className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5"
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h5 className="text-base font-bold font-display text-white capitalize">
                        {integ.integration}
                      </h5>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
                        v{integ.version}
                      </span>
                    </div>
                    <p className="text-[10.5px] font-mono text-slate-500 mt-1">
                      installed {integ.installedAt.slice(0, 10)}
                    </p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-extrabold text-cyan-300 font-display leading-none">
                      {integ.fileCount}
                    </div>
                    <div className="text-[10px] font-mono uppercase text-slate-400">
                      files
                    </div>
                  </div>
                </div>
                <details>
                  <summary className="text-[11px] font-mono text-cyan-300 cursor-pointer hover:text-cyan-200">
                    Show installed files
                  </summary>
                  <ul className="mt-2 space-y-1 max-h-64 overflow-y-auto pr-2 font-mono text-[10.5px]">
                    {integ.files.map((f) => (
                      <li
                        key={f}
                        className="text-slate-400 hover:text-slate-200 break-all"
                      >
                        {f}
                      </li>
                    ))}
                  </ul>
                </details>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Templates */}
      <div className="space-y-4">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
          <FileCode className="h-4 w-4 text-amber-400" />
          Templates
        </h4>
        {data.templates.length === 0 ? (
          <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 p-6 text-center text-[11px] font-mono text-slate-500 italic">
            No templates found under .specify/templates/.
          </div>
        ) : (
          <div className="space-y-2">
            {data.templates.map((t) => (
              <TemplateCard key={t.name} template={t} />
            ))}
          </div>
        )}
      </div>

      {/* Scripts + Constitution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
            <Terminal className="h-4 w-4 text-emerald-400" />
            Bash scripts
          </h4>
          {data.scripts.length === 0 ? (
            <p className="text-[11px] font-mono text-slate-500 italic">
              No scripts under .specify/scripts/bash/.
            </p>
          ) : (
            <ul className="space-y-1.5 font-mono text-[11px]">
              {data.scripts.map((s) => (
                <li
                  key={s}
                  className="flex items-center gap-2 text-slate-300"
                >
                  <GitBranch className="h-3 w-3 text-slate-500" />
                  <code className="text-cyan-300">{s}</code>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
            <BookOpen className="h-4 w-4 text-rose-400" />
            Project constitution
          </h4>
          {data.constitution ? (
            <>
              <div className="flex items-center gap-2 mb-2">
                {constitutionStatus && (
                  <span
                    className={`px-2 py-0.5 rounded-full border text-[10px] font-mono uppercase flex items-center gap-1 ${constitutionStatus.cls}`}
                  >
                    {constitutionStatus.icon}
                    {constitutionStatus.label}
                  </span>
                )}
                <span className="text-[10.5px] font-mono text-slate-500">
                  {data.constitution.lines} lines · {data.constitution.bytes} B
                </span>
              </div>
              {constitutionStatus?.note && (
                <p className="text-[11px] text-slate-400 mb-2 leading-relaxed">
                  {constitutionStatus.note}
                </p>
              )}
              <pre className="p-3 text-[10.5px] font-mono text-slate-300 bg-slate-950/80 border border-slate-800/80 rounded-xl overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-64">
                {data.constitution.preview}
                {data.constitution.lines > 20 && (
                  <span className="text-slate-500">
                    {"\n… "}
                    ({data.constitution.lines - 20} more lines)
                  </span>
                )}
              </pre>
              <p className="text-[10px] font-mono text-slate-500 mt-2">
                Source: <code className="text-cyan-300">{data.constitution.path}</code>
              </p>
            </>
          ) : (
            <p className="text-[11px] font-mono text-slate-500 italic">
              memory/constitution.md not created yet.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default SpecKitPanel;
