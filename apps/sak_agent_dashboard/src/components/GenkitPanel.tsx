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
  Radio,
  Rocket,
  Sparkles,
  Wrench,
} from "lucide-react";
import {
  GenkitData,
  GenkitPrimitive,
  GenkitPrimitiveKind,
} from "@/lib/types";

interface GenkitPanelProps {
  data: GenkitData | null;
}

const KIND_ICON: Record<GenkitPrimitiveKind, React.ReactNode> = {
  core: <Boxes className="h-3.5 w-3.5 text-cyan-300" />,
  decorator: <Wrench className="h-3.5 w-3.5 text-emerald-300" />,
  generation: <Radio className="h-3.5 w-3.5 text-sky-300" />,
  session: <Layers className="h-3.5 w-3.5 text-purple-300" />,
  model: <Cpu className="h-3.5 w-3.5 text-amber-300" />,
};

const KIND_ACCENT: Record<GenkitPrimitiveKind, string> = {
  core: "text-cyan-300 border-cyan-500/40 bg-cyan-500/10",
  decorator: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10",
  generation: "text-sky-300 border-sky-500/40 bg-sky-500/10",
  session: "text-purple-300 border-purple-500/40 bg-purple-500/10",
  model: "text-amber-300 border-amber-500/40 bg-amber-500/10",
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

function PrimitiveCard({ primitive }: { primitive: GenkitPrimitive }) {
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

export function GenkitPanel({ data }: GenkitPanelProps) {
  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-cyan-400" />
            Genkit
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Loading Genkit SDK inventory…
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
            <Sparkles className="h-5 w-5 text-cyan-400" />
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
              genkit-ai/genkit-python
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

      {/* Install + distinctive features */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
            <Package className="h-4 w-4 text-emerald-400" />
            Install
          </h4>
          <div className="rounded-lg border border-slate-800/80 bg-slate-950/80 overflow-hidden">
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800/80 bg-slate-900/70">
              <span className="text-[10px] font-mono text-slate-400 uppercase">
                uv add
              </span>
              <CopyButton payload={data.install} />
            </div>
            <pre className="p-3 text-[11px] font-mono text-cyan-300 overflow-x-auto whitespace-pre-wrap">
              {data.install}
            </pre>
          </div>
        </div>
        <div className="lg:col-span-2 glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
            <Sparkles className="h-4 w-4 text-cyan-400" />
            Distinctive features
          </h4>
          <ul className="space-y-2 text-[11px] text-slate-300 leading-relaxed">
            {data.distinctiveFeatures.map((f, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <Check className="h-3.5 w-3.5 text-emerald-400 mt-0.5 shrink-0" />
                <span>{f}</span>
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

      {/* Provider ecosystem */}
      <div>
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Cpu className="h-4 w-4 text-amber-400" />
          Model providers
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.providers.map((p) => (
            <div
              key={p.id}
              className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl"
            >
              <div className="flex items-center justify-between mb-1">
                <h5 className="text-sm font-bold font-display text-white tracking-tight">
                  {p.name}
                </h5>
                <span
                  className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-full border ${
                    p.supported
                      ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/40"
                      : "bg-slate-700/40 text-slate-400 border-slate-600/40"
                  }`}
                >
                  {p.supported ? "supported" : "planned"}
                </span>
              </div>
              <code className="text-[11px] font-mono text-cyan-300">
                {p.packageName}
              </code>
              <p className="text-[11px] text-slate-400 leading-relaxed mt-1.5">
                {p.description}
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
    </div>
  );
}

export default GenkitPanel;
