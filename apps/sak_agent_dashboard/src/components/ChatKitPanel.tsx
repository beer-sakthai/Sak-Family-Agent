"use client";

import React, { useState } from "react";
import {
  Check,
  Copy,
  ExternalLink,
  GitBranch,
  Globe,
  Key,
  MessagesSquare,
  Package,
  Server,
  Sparkles,
  Terminal,
} from "lucide-react";
import { ChatKitCapability, ChatKitData, ChatKitSample } from "@/lib/types";

interface ChatKitPanelProps {
  data: ChatKitData | null;
}

const SAMPLE_ACCENTS: Record<string, string> = {
  "cat-lounge": "from-amber-500/25 to-rose-500/25 border-amber-500/30",
  "customer-support": "from-cyan-500/25 to-blue-600/25 border-cyan-500/30",
  "news-guide": "from-purple-500/25 to-fuchsia-500/25 border-purple-500/30",
  "metro-map": "from-emerald-500/25 to-teal-500/25 border-emerald-500/30",
};

const CAPABILITY_ACCENT: Record<ChatKitCapability, string> = {
  "server-tools": "bg-cyan-500/10 text-cyan-300 border-cyan-500/40",
  "client-state": "bg-purple-500/10 text-purple-300 border-purple-500/40",
  widgets: "bg-emerald-500/10 text-emerald-300 border-emerald-500/40",
  "widget-actions": "bg-teal-500/10 text-teal-300 border-teal-500/40",
  attachments: "bg-amber-500/10 text-amber-300 border-amber-500/40",
  "speech-input": "bg-sky-500/10 text-sky-300 border-sky-500/40",
  "entity-tagging": "bg-fuchsia-500/10 text-fuchsia-300 border-fuchsia-500/40",
  "dynamic-thread-titles":
    "bg-rose-500/10 text-rose-300 border-rose-500/40",
  "image-generation": "bg-pink-500/10 text-pink-300 border-pink-500/40",
  "route-visualization":
    "bg-lime-500/10 text-lime-300 border-lime-500/40",
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
      aria-label="Copy command"
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

function SampleCard({
  sample,
  labels,
}: {
  sample: ChatKitSample;
  labels: Record<ChatKitCapability, string>;
}) {
  const [runMode, setRunMode] = useState<"root" | "standalone">("root");
  const command =
    runMode === "root" ? sample.runCommandFromRoot : sample.runCommandStandalone;
  const accent =
    SAMPLE_ACCENTS[sample.id] ??
    "from-slate-500/25 to-slate-700/25 border-slate-500/30";
  return (
    <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden">
      <div className={`p-5 border-b border-slate-800/70 bg-gradient-to-br ${accent}`}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h5 className="text-lg font-bold font-display text-white tracking-tight flex items-center gap-2">
              <MessagesSquare className="h-5 w-5 text-white/90" />
              {sample.displayName}
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-black/40 text-white border border-white/20">
                :{sample.port}
              </span>
            </h5>
            <p className="text-[11px] font-mono text-white/80 mt-0.5 uppercase tracking-wide">
              {sample.domain}
            </p>
          </div>
        </div>
      </div>
      <div className="p-5 space-y-4">
        <p className="text-[12px] text-slate-300 leading-relaxed">
          {sample.description}
        </p>

        {/* Stack */}
        <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <div className="text-[10px] uppercase text-slate-500 mb-0.5">
              Frontend
            </div>
            <div className="text-slate-200">{sample.frontend}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <div className="text-[10px] uppercase text-slate-500 mb-0.5">
              Backend
            </div>
            <div className="text-slate-200">{sample.backend}</div>
          </div>
        </div>

        {/* Capabilities */}
        <div>
          <div className="text-[10px] font-mono uppercase text-slate-500 mb-1.5">
            Capabilities demonstrated
          </div>
          <div className="flex flex-wrap gap-1.5">
            {sample.capabilities.map((c) => (
              <span
                key={c}
                className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border ${CAPABILITY_ACCENT[c]}`}
              >
                {labels[c]}
              </span>
            ))}
          </div>
        </div>

        {/* Highlights */}
        <ul className="space-y-1.5 text-[11px] text-slate-300 leading-relaxed">
          {sample.highlights.map((h, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <Sparkles className="h-3 w-3 text-cyan-400 mt-1 shrink-0" />
              <span>{h}</span>
            </li>
          ))}
        </ul>

        {/* Run block */}
        <div className="rounded-xl border border-slate-800/80 bg-slate-950/80 overflow-hidden">
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800/80 bg-slate-900/70">
            <div className="flex items-center gap-1">
              <button
                onClick={() => setRunMode("root")}
                className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border ${
                  runMode === "root"
                    ? "bg-cyan-500/15 text-cyan-200 border-cyan-500/40"
                    : "bg-slate-800/60 text-slate-400 border-slate-700/60 hover:text-slate-200"
                }`}
              >
                from repo root
              </button>
              <button
                onClick={() => setRunMode("standalone")}
                className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border ${
                  runMode === "standalone"
                    ? "bg-cyan-500/15 text-cyan-200 border-cyan-500/40"
                    : "bg-slate-800/60 text-slate-400 border-slate-700/60 hover:text-slate-200"
                }`}
              >
                standalone
              </button>
            </div>
            <CopyButton payload={command} />
          </div>
          <pre className="p-3 text-[11px] font-mono text-cyan-300 overflow-x-auto">
            {command}
          </pre>
        </div>
      </div>
    </div>
  );
}

export function ChatKitPanel({ data }: ChatKitPanelProps) {
  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <MessagesSquare className="h-5 w-5 text-cyan-400" />
            ChatKit Samples
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Loading ChatKit sample inventory…
          </p>
        </div>
      </div>
    );
  }

  // Union of capabilities across samples, in declaration order
  const orderedCaps: ChatKitCapability[] = (
    Object.keys(data.capabilityLabels) as ChatKitCapability[]
  ).filter((c) => data.samples.some((s) => s.capabilities.includes(c)));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <MessagesSquare className="h-5 w-5 text-cyan-400" />
            {data.overview.title}
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60">
              {data.samples.length} samples
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
            openai/openai-chatkit-advanced-samples
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>

      {/* Prerequisites */}
      <div>
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Key className="h-4 w-4 text-amber-400" />
          Prerequisites
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {data.prerequisites.map((p) => (
            <div
              key={p.label}
              className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[13px] font-bold text-white font-display">
                  {p.label}
                </span>
                {p.envVar && (
                  <code className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700/70">
                    {p.envVar}
                  </code>
                )}
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                {p.detail}
              </p>
              {p.installCommand && (
                <div className="mt-2 rounded-lg border border-slate-800/80 bg-slate-950/80 overflow-hidden">
                  <div className="flex items-center justify-between px-2.5 py-1 border-b border-slate-800/80 bg-slate-900/70">
                    <span className="text-[10px] font-mono text-slate-500 uppercase">
                      install
                    </span>
                    <CopyButton payload={p.installCommand} />
                  </div>
                  <pre className="p-2.5 text-[10.5px] font-mono text-cyan-300 overflow-x-auto">
                    {p.installCommand}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Samples grid */}
      <div className="space-y-4">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
          <Package className="h-4 w-4 text-cyan-400" />
          Sample apps
        </h4>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {data.samples.map((s) => (
            <SampleCard
              key={s.id}
              sample={s}
              labels={data.capabilityLabels}
            />
          ))}
        </div>
      </div>

      {/* Capability matrix */}
      <div className="space-y-3">
        <div>
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-emerald-400" />
            Capability matrix
          </h4>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Which ChatKit primitives each sample exercises. Use this to pick the
            sample closest to what you want to build.
          </p>
        </div>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Capability</th>
                  {data.samples.map((s) => (
                    <th key={s.id} className="px-4 py-2.5 text-center">
                      {s.displayName}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {orderedCaps.map((cap) => (
                  <tr key={cap} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-3">
                      <span
                        className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border ${CAPABILITY_ACCENT[cap]}`}
                      >
                        {data.capabilityLabels[cap]}
                      </span>
                    </td>
                    {data.samples.map((s) => (
                      <td
                        key={`${s.id}-${cap}`}
                        className="px-4 py-3 text-center"
                      >
                        {s.capabilities.includes(cap) ? (
                          <Check className="h-4 w-4 text-emerald-400 inline" />
                        ) : (
                          <span className="text-slate-700">·</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Quick-start block */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Terminal className="h-4 w-4 text-emerald-400" />
          Try one from a fresh clone
        </h4>
        <div className="rounded-xl border border-slate-800/80 bg-slate-950/80 overflow-hidden">
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800/80 bg-slate-900/70">
            <span className="text-[10px] font-mono text-slate-400 uppercase inline-flex items-center gap-1.5">
              <Server className="h-3 w-3 text-cyan-400" /> bash
            </span>
            <CopyButton
              payload={`git clone https://github.com/openai/openai-chatkit-advanced-samples.git
cd openai-chatkit-advanced-samples
export OPENAI_API_KEY=sk-...
npm install
npm run cat-lounge   # then open http://localhost:5170`}
            />
          </div>
          <pre className="p-4 text-[11px] font-mono text-slate-200 overflow-x-auto leading-relaxed">
{`git clone https://github.com/openai/openai-chatkit-advanced-samples.git
cd openai-chatkit-advanced-samples
export OPENAI_API_KEY=sk-...
npm install
npm run cat-lounge   # then open `}
            <span className="text-cyan-300">http://localhost:5170</span>
          </pre>
        </div>
        <p className="text-[11px] text-slate-500 mt-2 font-mono flex items-center gap-1.5">
          <Globe className="h-3 w-3" />
          Each sample runs on its own port (5170 · 5171 · 5172 · 5173) — safe
          to run several side by side.
        </p>
      </div>
    </div>
  );
}

export default ChatKitPanel;
