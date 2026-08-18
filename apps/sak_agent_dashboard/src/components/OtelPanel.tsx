"use client";

import React, { useState } from "react";
import {
  Activity,
  BarChart3,
  Check,
  Copy,
  ExternalLink,
  FileText,
  GitBranch,
  Package,
  Radio,
  ScrollText,
  Send,
  Telescope,
} from "lucide-react";
import { GithubIcon as Github } from "./GithubIcon";
import { OtelData, OtelSignal } from "@/lib/types";

interface OtelPanelProps {
  data: OtelData | null;
}

const SIGNAL_ICON: Record<OtelSignal, React.ReactNode> = {
  traces: <Activity className="h-4 w-4 text-cyan-300" />,
  metrics: <BarChart3 className="h-4 w-4 text-emerald-300" />,
  logs: <ScrollText className="h-4 w-4 text-amber-300" />,
};

const SIGNAL_ACCENT: Record<OtelSignal, string> = {
  traces: "border-cyan-500/40 bg-cyan-500/[0.06]",
  metrics: "border-emerald-500/40 bg-emerald-500/[0.06]",
  logs: "border-amber-500/40 bg-amber-500/[0.06]",
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

export function OtelPanel({ data }: OtelPanelProps) {
  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Telescope className="h-5 w-5 text-cyan-400" />
            Observability (OpenTelemetry)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Loading OTel inventory…</p>
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
            <Telescope className="h-5 w-5 text-cyan-400" />
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
              open-telemetry/opentelemetry.io
              <ExternalLink className="h-3 w-3" />
            </a>
            <a
              href={data.overview.siteUrl}
              target="_blank"
              rel="noreferrer noopener"
              className="inline-flex items-center gap-1.5 text-[11px] font-mono text-cyan-300 hover:text-cyan-200"
            >
              <FileText className="h-3.5 w-3.5" />
              opentelemetry.io
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </div>

      {/* Install */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Package className="h-4 w-4 text-emerald-400" />
          Python install (API + SDK + OTLP exporter)
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

      {/* Signals */}
      <div>
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Radio className="h-4 w-4 text-cyan-400" />
          Signals
        </h4>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {data.signals.map((s) => (
            <div
              key={s.id}
              className={`p-5 rounded-2xl bg-slate-900/80 border backdrop-blur-xl ${SIGNAL_ACCENT[s.id]}`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {SIGNAL_ICON[s.id]}
                  <h5 className="text-sm font-bold font-display text-white tracking-tight uppercase">
                    {s.title}
                  </h5>
                </div>
                <a
                  href={s.docsUrl}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="text-[10px] font-mono text-cyan-300 hover:text-cyan-200 inline-flex items-center gap-1"
                >
                  docs <ExternalLink className="h-3 w-3" />
                </a>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed">{s.summary}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {s.keyPrimitives.map((p) => (
                  <span
                    key={p}
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/60"
                  >
                    {p}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Exporters */}
      <div>
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Send className="h-4 w-4 text-emerald-400" />
          Exporters worth knowing
        </h4>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 overflow-hidden">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-4 py-2.5">Exporter</th>
                <th className="px-4 py-2.5">Transport</th>
                <th className="px-4 py-2.5">When to use</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {data.exporters.map((e) => (
                <tr key={e.id} className="hover:bg-slate-800/40 transition-colors align-top">
                  <td className="px-4 py-3 font-bold text-white">{e.name}</td>
                  <td className="px-4 py-3 text-cyan-300 whitespace-nowrap">{e.transport}</td>
                  <td className="px-4 py-3 leading-relaxed">{e.usage}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Semconv for LLMs */}
      <div>
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <FileText className="h-4 w-4 text-amber-400" />
          GenAI semantic conventions (draft)
        </h4>
        <p className="text-[11px] text-slate-400 mb-3 leading-relaxed max-w-3xl">
          The attributes below are the shared names every OTel-instrumented LLM
          Emitting these from sakthai&apos;s agent loop
          would let a single backend (Jaeger, Grafana, GCP Trace) render every
          persona&apos;s runs uniformly.
        </p>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 overflow-hidden">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-4 py-2.5">Attribute</th>
                <th className="px-4 py-2.5">Purpose</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {data.llmSemconv.map((a) => (
                <tr key={a.attribute} className="hover:bg-slate-800/40 transition-colors align-top">
                  <td className="px-4 py-3 text-cyan-300 whitespace-nowrap">
                    {a.attribute}
                  </td>
                  <td className="px-4 py-3 leading-relaxed">{a.purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Sakthai integration snippet */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800/70 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
              <Activity className="h-4 w-4 text-cyan-400" />
              Proposed wiring for sakthai/agent/loop.py
            </h4>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Target integration shape — not in-tree yet.
            </p>
          </div>
          <CopyButton payload={data.sakthaiIntegration} />
        </div>
        <pre className="p-4 text-[11px] font-mono text-slate-200 bg-slate-950/80 overflow-x-auto leading-relaxed">
          {data.sakthaiIntegration}
        </pre>
      </div>
    </div>
  );
}

export default OtelPanel;
