"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  Ban,
  Check,
  Copy,
  ExternalLink,
  Fingerprint,
  GitBranch,
  KeyRound,
  Package,
  Rocket,
  Route,
  ShieldCheck,
  Split,
  Wrench,
} from "lucide-react";
import { GithubIcon as Github } from "./GithubIcon";
import { DEFAULT_M365_ADAPTER, M365CopilotAdapter } from "@/lib/m365/adapter";
import { M365CopilotData, M365CopilotPrimitive } from "@/lib/types";

interface M365CopilotPanelProps {
  data: M365CopilotData | null;
  /** Injectable adapter; defaults to the static-docs adapter. */
  adapter?: M365CopilotAdapter;
}

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

function PrimitiveCard({ primitive }: { primitive: M365CopilotPrimitive }) {
  return (
    <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden">
      <div className="p-4 border-b border-slate-800/70 flex items-start justify-between gap-3">
        <div>
          <h5 className="text-sm font-bold font-display text-white tracking-tight">
            {primitive.name}
          </h5>
          <p className="text-[11px] text-slate-400 mt-1 leading-relaxed max-w-2xl">
            {primitive.summary}
          </p>
        </div>
        <CopyButton payload={primitive.snippet} />
      </div>
      <pre className="p-4 text-[11px] font-mono text-slate-200 bg-slate-950/80 overflow-x-auto leading-relaxed">
        {primitive.snippet}
      </pre>
    </div>
  );
}

export function M365CopilotPanel({ data, adapter = DEFAULT_M365_ADAPTER }: M365CopilotPanelProps) {
  const authStrategy = adapter.getAuthStrategy();
  const gate = authStrategy.accountTypeGate;

  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Fingerprint className="h-5 w-5 text-cyan-400" />
            M365 Copilot
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Loading Microsoft Agents M365Copilot inventory…
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
            <Fingerprint className="h-5 w-5 text-cyan-400" />
            {data.overview.title}
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60">
              {data.overview.authModel}
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
              microsoft/Agents-M365Copilot
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

      {/* Account-type blocker — surfaced high, before the install steps */}
      <div className="glass-panel rounded-2xl border-2 border-amber-500/50 bg-amber-500/[0.06] backdrop-blur-xl p-5">
        <h4 className="text-base font-bold font-display text-white tracking-tight flex items-center gap-2 mb-2">
          <AlertTriangle className="h-5 w-5 text-amber-400" />
          {gate.headline}
        </h4>
        <p className="text-[11.5px] text-slate-200 leading-relaxed max-w-3xl">
          {gate.body}
        </p>

        <div className="mt-4">
          <h5 className="text-[10px] font-mono uppercase tracking-wider text-rose-300 flex items-center gap-1.5 mb-2">
            <Ban className="h-3 w-3" />
            Also ruled out
          </h5>
          <ul className="space-y-1.5 text-[11px] text-slate-300 leading-relaxed">
            {gate.ruledOutAlternatives.map((a, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-rose-400 mt-0.5">✕</span>
                <span>{a}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-4 p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/[0.05]">
          <h5 className="text-[10px] font-mono uppercase tracking-wider text-emerald-300 flex items-center gap-1.5 mb-1.5">
            <Route className="h-3 w-3" />
            The path that does work
          </h5>
          <p className="text-[11px] text-slate-200 leading-relaxed">
            {gate.viablePath}
          </p>
        </div>

        <p className="text-[10.5px] font-mono text-slate-500 mt-3">
          source: <code className="text-cyan-300">{gate.specPath}</code>
        </p>
      </div>

      {/* Install */}
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

      {/* Quickstart */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800/70 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Rocket className="h-4 w-4 text-cyan-400" />
            <h4 className="text-sm font-bold font-display text-white tracking-tight">
              Quickstart
            </h4>
          </div>
          <CopyButton payload={data.quickstart} />
        </div>
        <pre className="p-4 text-[11.5px] font-mono text-slate-200 bg-slate-950/80 overflow-x-auto leading-relaxed">
          {data.quickstart}
        </pre>
      </div>

      {/* Delegated-auth walkthrough */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <KeyRound className="h-4 w-4 text-amber-400" />
          {authStrategy.name}
        </h4>
        <ol className="space-y-2">
          {data.authSteps.map((s, idx) => (
            <li
              key={idx}
              className="flex items-start gap-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800/80"
            >
              <span className="text-[11px] font-mono text-slate-500 mt-0.5">
                {String(idx + 1).padStart(2, "0")}
              </span>
              <span className="text-[11.5px] text-slate-300 leading-relaxed">
                {s}
              </span>
            </li>
          ))}
        </ol>
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

      {/* Contrast with teams-copilot-mcp */}
      <div className="space-y-3">
        <div>
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Split className="h-4 w-4 text-fuchsia-400" />
            vs. teams-copilot-mcp (in the MCP Servers tab)
          </h4>
          <p className="text-[11px] text-slate-400 mt-0.5 max-w-3xl leading-relaxed">
            Both hit the Microsoft Graph surface for the persona work, but
            through completely different auth and transport shapes. Pick per
            use case; they can coexist.
          </p>
        </div>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Dimension</th>
                  <th className="px-4 py-2.5">
                    <span className="text-cyan-300 flex items-center gap-1">
                      <ShieldCheck className="h-3 w-3" />
                      m365 SDK
                    </span>
                  </th>
                  <th className="px-4 py-2.5">
                    <span className="text-fuchsia-300">teams-copilot-mcp</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {data.contrastWithTeamsMcp.map((row) => (
                  <tr
                    key={row.dimension}
                    className="hover:bg-slate-800/40 transition-colors align-top"
                  >
                    <td className="px-4 py-3 text-slate-400 font-bold whitespace-nowrap">
                      {row.dimension}
                    </td>
                    <td className="px-4 py-3 text-slate-200 leading-relaxed">
                      {row.m365Sdk}
                    </td>
                    <td className="px-4 py-3 text-slate-200 leading-relaxed">
                      {row.teamsCopilotMcp}
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

export default M365CopilotPanel;
