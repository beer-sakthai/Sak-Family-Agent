"use client";

import React, { useState } from "react";
import {
  BookOpen,
  Check,
  ClipboardList,
  Copy,
  ExternalLink,
  FileCode,
  GitBranch,
  Music2,
  Play,
  Rocket,
  Route,
  ShieldCheck,
  Terminal,
  Undo2,
  Wrench,
} from "lucide-react";
import { ConductorData, ConductorCommand } from "@/lib/types";

interface ConductorPanelProps {
  data: ConductorData | null;
}

const CATEGORY_ICON: Record<ConductorCommand["category"], React.ReactNode> = {
  setup: <Wrench className="h-3.5 w-3.5 text-emerald-300" />,
  track: <Route className="h-3.5 w-3.5 text-cyan-300" />,
  implement: <Rocket className="h-3.5 w-3.5 text-amber-300" />,
  status: <ClipboardList className="h-3.5 w-3.5 text-purple-300" />,
  revert: <Undo2 className="h-3.5 w-3.5 text-rose-300" />,
  review: <ShieldCheck className="h-3.5 w-3.5 text-sky-300" />,
};

const CATEGORY_ACCENT: Record<ConductorCommand["category"], string> = {
  setup: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10",
  track: "text-cyan-300 border-cyan-500/40 bg-cyan-500/10",
  implement: "text-amber-300 border-amber-500/40 bg-amber-500/10",
  status: "text-purple-300 border-purple-500/40 bg-purple-500/10",
  revert: "text-rose-300 border-rose-500/40 bg-rose-500/10",
  review: "text-sky-300 border-sky-500/40 bg-sky-500/10",
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
      aria-label="Copy"
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

export function ConductorPanel({ data }: ConductorPanelProps) {
  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Music2 className="h-5 w-5 text-cyan-400" />
            Conductor
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Loading Conductor inventory…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Music2 className="h-5 w-5 text-cyan-400" />
            {data.overview.title}
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60">
              {data.overview.methodology}
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
            {data.overview.description}
          </p>
          <a
            href={data.overview.repoUrl}
            target="_blank"
            rel="noreferrer noopener"
            className="mt-1.5 inline-flex items-center gap-1.5 text-[11px] font-mono text-cyan-300 hover:text-cyan-200"
          >
            <GitBranch className="h-3.5 w-3.5" />
            gemini-cli-extensions/conductor
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>

      {/* Host install cards */}
      <div>
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Terminal className="h-4 w-4 text-emerald-400" />
          Install per host
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {data.hosts.map((h) => (
            <div
              key={h.id}
              className={`p-4 rounded-2xl bg-slate-900/80 border backdrop-blur-xl ${
                h.primary
                  ? "border-emerald-500/40 shadow-lg shadow-emerald-950/30"
                  : "border-slate-800/80"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <h5 className="text-sm font-bold font-display text-white tracking-tight">
                  {h.name}
                </h5>
                {h.primary && (
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-full border bg-emerald-500/10 text-emerald-300 border-emerald-500/40">
                    recommended
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed mb-2">
                {h.note}
              </p>
              <div className="rounded-lg border border-slate-800/80 bg-slate-950/80 overflow-hidden">
                <div className="flex items-center justify-between px-2.5 py-1 border-b border-slate-800/80 bg-slate-900/70">
                  <span className="text-[10px] font-mono text-slate-400 uppercase">
                    install
                  </span>
                  <CopyButton payload={h.installCommand} />
                </div>
                <pre className="p-2.5 text-[11px] font-mono text-cyan-300 overflow-x-auto whitespace-pre-wrap">
                  {h.installCommand}
                </pre>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Command table */}
      <div className="space-y-3">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
          <Play className="h-4 w-4 text-cyan-400" />
          Slash commands
        </h4>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Kind</th>
                  <th className="px-4 py-2.5">Command</th>
                  <th className="px-4 py-2.5">Purpose</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {data.commands.map((c) => (
                  <tr
                    key={c.slash}
                    className="hover:bg-slate-800/40 transition-colors align-top"
                  >
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-full border ${CATEGORY_ACCENT[c.category]}`}
                      >
                        {CATEGORY_ICON[c.category]}
                        {c.category}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-cyan-300 whitespace-nowrap">
                      {c.slash}
                    </td>
                    <td className="px-4 py-3 text-slate-300 leading-relaxed max-w-2xl">
                      {c.purpose}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Workflow */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Route className="h-4 w-4 text-cyan-400" />
          Typical cycle
        </h4>
        <ol className="space-y-2">
          {data.workflow.map((step, idx) => (
            <li
              key={idx}
              className="flex items-start gap-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800/80"
            >
              <span className="text-[11px] font-mono text-slate-500 mt-0.5">
                {String(idx + 1).padStart(2, "0")}
              </span>
              <span className="text-[11.5px] text-slate-300 leading-relaxed">
                {step}
              </span>
            </li>
          ))}
        </ol>
      </div>

      {/* Generated artifacts */}
      <div className="space-y-3">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
          <FileCode className="h-4 w-4 text-amber-400" />
          Generated artifacts
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data.artifacts.map((a) => (
            <div
              key={a.path}
              className={`p-4 rounded-2xl border backdrop-blur-xl ${
                a.scope === "project"
                  ? "bg-slate-900/80 border-slate-800/80"
                  : "bg-purple-500/[0.04] border-purple-500/30"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <code className="text-[12px] font-mono text-white font-semibold break-all">
                  {a.path}
                </code>
                <span
                  className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-full border ${
                    a.scope === "project"
                      ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/40"
                      : "bg-purple-500/10 text-purple-300 border-purple-500/40"
                  }`}
                >
                  {a.scope}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">{a.purpose}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Cross-reference to SpecKit tab */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-2">
          <BookOpen className="h-4 w-4 text-fuchsia-400" />
          Relative to the SpecKit tab
        </h4>
        <p className="text-[11.5px] text-slate-300 leading-relaxed">
          Conductor and SpecKit are both spec-driven-development tools, but
          they live at different layers. SpecKit is workflow tooling installed
          into this repo (<code className="text-cyan-300">.specify/</code>) and
          runs specify → plan → tasks → implement as a general-purpose SDD
          cycle. Conductor is an agent plugin — installed into the
          <em> agent&apos;s</em> plugin dir, not the project — that turns any active
          agent (Antigravity or Claude Code) into a project manager that
          enforces the same SDD discipline. Use Conductor when you want the
          agent itself to own the loop; use SpecKit when the workflow lives in
          CI or a human-driven pipeline.
        </p>
      </div>
    </div>
  );
}

export default ConductorPanel;
