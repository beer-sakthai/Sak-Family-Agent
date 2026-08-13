"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  Bot,
  Check,
  Copy,
  ExternalLink,
  FileCode,
  GitBranch,
  Layers,
  MessagesSquare,
  Package,
  Radio,
  Rocket,
  Settings,
  ShieldCheck,
  Sparkles,
  Wrench,
  Zap,
} from "lucide-react";
import {
  AntigravityData,
  AntigravityPrimitive,
  AntigravityPrimitiveKind,
} from "@/lib/types";

interface AntigravityPanelProps {
  data: AntigravityData | null;
}

const KIND_ICON: Record<AntigravityPrimitiveKind, React.ReactNode> = {
  agent: <Bot className="h-3.5 w-3.5 text-cyan-300" />,
  config: <Settings className="h-3.5 w-3.5 text-emerald-300" />,
  conversation: <MessagesSquare className="h-3.5 w-3.5 text-purple-300" />,
  response: <Radio className="h-3.5 w-3.5 text-sky-300" />,
  loop: <Rocket className="h-3.5 w-3.5 text-amber-300" />,
  tool: <Wrench className="h-3.5 w-3.5 text-emerald-300" />,
  hook: <ShieldCheck className="h-3.5 w-3.5 text-rose-300" />,
  mcp: <Layers className="h-3.5 w-3.5 text-fuchsia-300" />,
};

const KIND_ACCENT: Record<AntigravityPrimitiveKind, string> = {
  agent: "text-cyan-300 border-cyan-500/40 bg-cyan-500/10",
  config: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10",
  conversation: "text-purple-300 border-purple-500/40 bg-purple-500/10",
  response: "text-sky-300 border-sky-500/40 bg-sky-500/10",
  loop: "text-amber-300 border-amber-500/40 bg-amber-500/10",
  tool: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10",
  hook: "text-rose-300 border-rose-500/40 bg-rose-500/10",
  mcp: "text-fuchsia-300 border-fuchsia-500/40 bg-fuchsia-500/10",
};

const FEATURE_ICON: Record<string, React.ReactNode> = {
  multimodal: <Sparkles className="h-4 w-4 text-purple-300" />,
  tools: <Wrench className="h-4 w-4 text-emerald-300" />,
  mcp: <Layers className="h-4 w-4 text-fuchsia-300" />,
  policy: <ShieldCheck className="h-4 w-4 text-rose-300" />,
  background: <Zap className="h-4 w-4 text-amber-300" />,
  streaming: <Radio className="h-4 w-4 text-sky-300" />,
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

function PrimitiveCard({ primitive }: { primitive: AntigravityPrimitive }) {
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

export function AntigravityPanel({ data }: AntigravityPanelProps) {
  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Bot className="h-5 w-5 text-cyan-400" />
            Antigravity
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Loading Antigravity SDK inventory…
          </p>
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
            <Bot className="h-5 w-5 text-cyan-400" />
            {data.overview.title}
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60">
              {data.overview.license}
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
              google-antigravity/antigravity-sdk-python
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
            <span className="text-[11px] font-mono text-slate-500">
              by {data.overview.author}
            </span>
          </div>
        </div>
      </div>

      {/* Install + warning */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
            <Package className="h-4 w-4 text-emerald-400" />
            Install
          </h4>
          <div className="rounded-lg border border-slate-800/80 bg-slate-950/80 overflow-hidden">
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800/80 bg-slate-900/70">
              <span className="text-[10px] font-mono text-slate-400 uppercase">
                pypi
              </span>
              <CopyButton payload={data.install.pypi} />
            </div>
            <pre className="p-3 text-[11px] font-mono text-cyan-300 overflow-x-auto">
              {data.install.pypi}
            </pre>
          </div>
        </div>
        <div className="lg:col-span-2 glass-panel rounded-2xl border p-5 border-amber-500/30 bg-amber-500/[0.04]">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            Wheels only — cloning the repo is not enough
          </h4>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            {data.install.warning}
          </p>
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

      {/* Feature grid */}
      <div>
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Sparkles className="h-4 w-4 text-emerald-400" />
          Core features
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.features.map((f) => (
            <div
              key={f.id}
              className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl"
            >
              <div className="flex items-center gap-2 mb-1">
                {FEATURE_ICON[f.category] ?? (
                  <FileCode className="h-4 w-4 text-slate-300" />
                )}
                <h5 className="text-sm font-bold font-display text-white tracking-tight">
                  {f.title}
                </h5>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                {f.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Primitives */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Wrench className="h-4 w-4 text-cyan-400" />
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

      {/* Comparison */}
      <div className="space-y-3">
        <div>
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Layers className="h-4 w-4 text-fuchsia-400" />
            Where this sits vs. the other SDK tabs
          </h4>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Antigravity is a full agent framework; ChatKit is a UI + samples
            layer; the MCP Python SDK is the wire protocol. Pick by what you
            need to build.
          </p>
        </div>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Dimension</th>
                  <th className="px-4 py-2.5">
                    <span className="text-cyan-300">Antigravity</span>
                  </th>
                  <th className="px-4 py-2.5">
                    <span className="text-fuchsia-300">ChatKit</span>
                  </th>
                  <th className="px-4 py-2.5">
                    <span className="text-emerald-300">MCP SDK</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {data.comparison.map((row) => (
                  <tr
                    key={row.dimension}
                    className="hover:bg-slate-800/40 transition-colors align-top"
                  >
                    <td className="px-4 py-3 text-slate-400 font-bold whitespace-nowrap">
                      {row.dimension}
                    </td>
                    <td className="px-4 py-3 text-slate-200 leading-relaxed">
                      {row.antigravity}
                    </td>
                    <td className="px-4 py-3 text-slate-200 leading-relaxed">
                      {row.chatkit}
                    </td>
                    <td className="px-4 py-3 text-slate-200 leading-relaxed">
                      {row.mcpSdk}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AntigravityPanel;
