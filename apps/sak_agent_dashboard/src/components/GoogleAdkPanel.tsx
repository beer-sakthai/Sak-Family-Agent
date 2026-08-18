"use client";

import React, { useState } from "react";
import {
  Boxes,
  Check,
  Copy,
  Cpu,
  ExternalLink,
  GitBranch,
  Layers,
  Package,
  Rocket,
  Split,
  Terminal,
  Users,
  Workflow,
  Wrench,
} from "lucide-react";
import { GithubIcon as Github } from "./GithubIcon";
import { AdkData, AdkPrimitive, AdkPrimitiveKind } from "@/lib/types";

interface GoogleAdkPanelProps {
  data: AdkData | null;
}

const KIND_ICON: Record<AdkPrimitiveKind, React.ReactNode> = {
  core: <Boxes className="h-3.5 w-3.5 text-cyan-300" />,
  "llm-agent": <Cpu className="h-3.5 w-3.5 text-cyan-300" />,
  "workflow-agent": <Split className="h-3.5 w-3.5 text-purple-300" />,
  runner: <Rocket className="h-3.5 w-3.5 text-amber-300" />,
  tool: <Wrench className="h-3.5 w-3.5 text-emerald-300" />,
  mcp: <Layers className="h-3.5 w-3.5 text-fuchsia-300" />,
  cli: <Terminal className="h-3.5 w-3.5 text-slate-300" />,
};

const KIND_ACCENT: Record<AdkPrimitiveKind, string> = {
  core: "text-cyan-300 border-cyan-500/40 bg-cyan-500/10",
  "llm-agent": "text-cyan-300 border-cyan-500/40 bg-cyan-500/10",
  "workflow-agent": "text-purple-300 border-purple-500/40 bg-purple-500/10",
  runner: "text-amber-300 border-amber-500/40 bg-amber-500/10",
  tool: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10",
  mcp: "text-fuchsia-300 border-fuchsia-500/40 bg-fuchsia-500/10",
  cli: "text-slate-300 border-slate-600/50 bg-slate-500/10",
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

function PrimitiveCard({ primitive }: { primitive: AdkPrimitive }) {
  return (
    <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden">
      <div className="p-4 border-b border-slate-800/70 flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <div className="mt-0.5 p-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
            {KIND_ICON[primitive.kind]}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h5 className="text-sm font-bold font-display text-white tracking-tight">
                {primitive.name}
              </h5>
              <span
                className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-full border ${KIND_ACCENT[primitive.kind]}`}
              >
                {primitive.kind}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1 leading-relaxed max-w-2xl">
              {primitive.summary}
            </p>
          </div>
        </div>
        <CopyButton payload={primitive.snippet} />
      </div>
      <pre className="p-4 text-[11px] font-mono text-slate-200 bg-slate-950/80 overflow-x-auto leading-relaxed">
        {primitive.snippet}
      </pre>
    </div>
  );
}

export function GoogleAdkPanel({ data }: GoogleAdkPanelProps) {
  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Users className="h-5 w-5 text-cyan-400" />
            Google ADK
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Loading ADK inventory…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Users className="h-5 w-5 text-cyan-400" />
            {data.overview.title}
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60">
              {data.overview.license}
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              Python {data.overview.pythonMin}
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
            {data.overview.description}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <a
              href={data.overview.repoUrl}
              target="_blank"
              rel="noreferrer noopener"
              className="inline-flex items-center gap-1.5 text-[11px] font-mono text-cyan-300 hover:text-cyan-200"
            >
              <GitBranch className="h-3.5 w-3.5" />
              google/adk-python
              <ExternalLink className="h-3 w-3" />
            </a>
            <a
              href={data.overview.pypiUrl}
              target="_blank"
              rel="noreferrer noopener"
              className="inline-flex items-center gap-1.5 text-[11px] font-mono text-cyan-300 hover:text-cyan-200"
            >
              <Package className="h-3.5 w-3.5" />
              {data.overview.packageName}
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </div>

      {/* Install + CLI */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
            <Package className="h-4 w-4 text-emerald-400" />
            Install
          </h4>
          <div className="rounded-lg border border-slate-800/80 bg-slate-950/80 overflow-hidden">
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800/80 bg-slate-900/70">
              <span className="text-[10px] font-mono text-slate-400 uppercase">pip</span>
              <CopyButton payload={data.install} />
            </div>
            <pre className="p-3 text-[11px] font-mono text-cyan-300 overflow-x-auto">
              {data.install}
            </pre>
          </div>
        </div>
        <div className="lg:col-span-2 glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
            <Terminal className="h-4 w-4 text-cyan-400" />
            CLI commands
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

      {/* Quickstart */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800/70 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Rocket className="h-4 w-4 text-cyan-400" />
            <h4 className="text-sm font-bold font-display text-white tracking-tight">
              Quickstart
            </h4>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              python
            </span>
          </div>
          <CopyButton payload={data.quickstart} />
        </div>
        <pre className="p-4 text-[11.5px] font-mono text-slate-200 bg-slate-950/80 overflow-x-auto leading-relaxed">
          {data.quickstart}
        </pre>
      </div>

      {/* Primitives */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Workflow className="h-4 w-4 text-cyan-400" />
            SDK primitives
          </h4>
          <span className="text-[11px] font-mono text-slate-500">
            {data.primitives.length} primitives · Python
          </span>
        </div>
        <div className="grid grid-cols-1 gap-3">
          {data.primitives.map((p) => (
            <PrimitiveCard key={p.id} primitive={p} />
          ))}
        </div>
      </div>

      {/* App container */}
      <div className="space-y-4">
        <div>
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Boxes className="h-4 w-4 text-cyan-400" />
            The App container
          </h4>
          <p className="text-[11px] text-slate-400 mt-1 max-w-3xl leading-relaxed">
            {data.app.intro}
          </p>
        </div>

        {/* Fields table */}
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Field</th>
                  <th className="px-4 py-2.5">Type</th>
                  <th className="px-4 py-2.5">Default</th>
                  <th className="px-4 py-2.5">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {data.app.fields.map((f) => (
                  <tr key={f.field} className="hover:bg-slate-800/40 transition-colors align-top">
                    <td className="px-4 py-3 text-cyan-300 whitespace-nowrap">{f.field}</td>
                    <td className="px-4 py-3 text-slate-400 whitespace-nowrap">{f.type}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border ${
                          f.defaultValue === "required"
                            ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                            : "bg-slate-700/40 text-slate-300 border-slate-600/40"
                        }`}
                      >
                        {f.defaultValue}
                      </span>
                    </td>
                    <td className="px-4 py-3 leading-relaxed max-w-xl">{f.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 border-t border-slate-800/70 bg-slate-950/40">
            <p className="text-[11px] text-slate-400 leading-relaxed">
              {data.app.nameRules}
            </p>
          </div>
        </div>

        {/* Plugins + configs */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
            <h5 className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
              <Wrench className="h-3 w-3 text-emerald-400" />
              Plugins
            </h5>
            <ul className="space-y-2">
              {data.app.plugins.map((p) => (
                <li
                  key={p.name}
                  className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80"
                >
                  <code className="text-[12px] font-mono text-white font-semibold">
                    {p.name}
                  </code>
                  <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                    {p.importPath}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                    {p.purpose}
                  </p>
                </li>
              ))}
            </ul>
          </div>
          <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
            <h5 className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
              <Layers className="h-3 w-3 text-purple-400" />
              Cross-cutting configs
            </h5>
            <ul className="space-y-2">
              {data.app.configs.map((c) => (
                <li
                  key={c.id}
                  className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80"
                >
                  <div className="flex items-center justify-between gap-2">
                    <code className="text-[12px] font-mono text-white font-semibold">
                      {c.name}
                    </code>
                    {c.experimental && (
                      <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 shrink-0">
                        experimental
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                    {c.importPath}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                    {c.purpose}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Config snippet */}
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden">
          <div className="p-4 border-b border-slate-800/70 flex items-center justify-between">
            <h5 className="text-sm font-bold font-display text-white tracking-tight">
              Configuring the cross-cutting features
            </h5>
            <CopyButton payload={data.app.configSnippet} />
          </div>
          <pre className="p-4 text-[11px] font-mono text-slate-200 bg-slate-950/80 overflow-x-auto leading-relaxed">
            {data.app.configSnippet}
          </pre>
        </div>

        {/* Legacy vs App */}
        <div className="glass-panel rounded-2xl border border-amber-500/30 bg-amber-500/[0.03] backdrop-blur-xl overflow-hidden">
          <div className="p-4 border-b border-amber-500/20 flex items-start justify-between gap-3">
            <div>
              <h5 className="text-sm font-bold font-display text-white tracking-tight">
                App versus a bare agent
              </h5>
              <p className="text-[11px] text-slate-400 mt-1 max-w-3xl leading-relaxed">
                {data.app.legacyNote}
              </p>
            </div>
            <CopyButton payload={data.app.legacySnippet} />
          </div>
          <pre className="p-4 text-[11px] font-mono text-slate-200 bg-slate-950/80 overflow-x-auto leading-relaxed">
            {data.app.legacySnippet}
          </pre>
          <ul className="p-4 space-y-1.5 text-[11px] text-slate-300 leading-relaxed">
            {data.app.legacyDifferences.map((d, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-amber-400 mt-0.5">•</span>
                <span>{d}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Limitations */}
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h5 className="text-sm font-bold font-display text-white tracking-tight mb-2">
            Limitations
          </h5>
          <ul className="space-y-1.5 text-[11px] text-slate-300 leading-relaxed">
            {data.app.limitations.map((l, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-rose-400 mt-0.5">•</span>
                <span>{l}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* A2A distributed */}
      <div className="space-y-4">
        <div>
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Split className="h-4 w-4 text-purple-400" />
            Agent-to-Agent (distributed topology)
          </h4>
          <p className="text-[11px] text-slate-400 mt-1 max-w-3xl leading-relaxed">
            {data.a2a.intro}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.a2a.services.map((s) => (
            <div
              key={s.name}
              className={`p-4 rounded-2xl bg-slate-900/80 border backdrop-blur-xl ${
                s.kind === "orchestrator"
                  ? "border-cyan-500/40"
                  : s.kind === "app"
                  ? "border-emerald-500/40"
                  : "border-slate-800/80"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <code className="text-[12px] font-mono text-white font-bold">
                  {s.name}
                </code>
                <span
                  className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-full border ${
                    s.kind === "orchestrator"
                      ? "bg-cyan-500/10 text-cyan-300 border-cyan-500/40"
                      : s.kind === "app"
                      ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/40"
                      : "bg-slate-700/40 text-slate-300 border-slate-600/40"
                  }`}
                >
                  {s.kind}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">{s.role}</p>
            </div>
          ))}
        </div>

        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden">
          <div className="p-4 border-b border-slate-800/70 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h5 className="text-sm font-bold font-display text-white tracking-tight">
                Orchestrator composing remote agents
              </h5>
              <code className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700/70">
                card: {data.a2a.agentCardPath}
              </code>
            </div>
            <CopyButton payload={data.a2a.snippet} />
          </div>
          <pre className="p-4 text-[11px] font-mono text-slate-200 bg-slate-950/80 overflow-x-auto leading-relaxed">
            {data.a2a.snippet}
          </pre>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
            <h5 className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
              Cloud Run environment
            </h5>
            <ul className="space-y-1.5 font-mono text-[11px]">
              {data.a2a.envVars.map((e) => (
                <li key={e.key} className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                  <code className="text-cyan-300">{e.key}</code>
                  <div className="text-slate-400 break-all mt-0.5">{e.value}</div>
                </li>
              ))}
            </ul>
          </div>
          <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
            <h5 className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
              Shared files (symlinked into each service)
            </h5>
            <ul className="space-y-2">
              {data.a2a.sharedFiles.map((f) => (
                <li key={f.file} className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80">
                  <code className="text-[11.5px] font-mono text-cyan-300">{f.file}</code>
                  <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                    {f.purpose}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Comparison note */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-2">
          <Layers className="h-4 w-4 text-fuchsia-400" />
          Where this sits vs. Antigravity + Genkit
        </h4>
        <p className="text-[11.5px] text-slate-300 leading-relaxed">
          {data.comparisonNote}
        </p>
      </div>
    </div>
  );
}

export default GoogleAdkPanel;
