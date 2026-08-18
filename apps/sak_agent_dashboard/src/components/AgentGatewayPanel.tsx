"use client";

import React, { useState } from "react";
import {
  Activity,
  Check,
  Copy,
  ExternalLink,
  Eye,
  Fingerprint,
  Globe,
  Lock,
  ScanSearch,
  Server,
  ShieldCheck,
  Terminal,
  Workflow,
} from "lucide-react";
import { GatewayControl, GatewayData } from "@/lib/types";

interface AgentGatewayPanelProps {
  data: GatewayData | null;
}

const CONTROL_ICON: Record<GatewayControl["kind"], React.ReactNode> = {
  authz: <Lock className="h-4 w-4 text-rose-300" />,
  content: <ScanSearch className="h-4 w-4 text-amber-300" />,
  discovery: <Workflow className="h-4 w-4 text-cyan-300" />,
  identity: <Fingerprint className="h-4 w-4 text-purple-300" />,
  observability: <Activity className="h-4 w-4 text-emerald-300" />,
};

const CONTROL_ACCENT: Record<GatewayControl["kind"], string> = {
  authz: "border-rose-500/40 bg-rose-500/[0.05]",
  content: "border-amber-500/40 bg-amber-500/[0.05]",
  discovery: "border-cyan-500/40 bg-cyan-500/[0.05]",
  identity: "border-purple-500/40 bg-purple-500/[0.05]",
  observability: "border-emerald-500/40 bg-emerald-500/[0.05]",
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

export function AgentGatewayPanel({ data }: AgentGatewayPanelProps) {
  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-cyan-400" />
            Agent Gateway
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Loading gateway inventory…</p>
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
            <ShieldCheck className="h-5 w-5 text-cyan-400" />
            {data.overview.title}
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60">
              {data.overview.license}
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
            {data.overview.description}
          </p>
          <a
            href={data.overview.codelabUrl}
            target="_blank"
            rel="noreferrer noopener"
            className="mt-1.5 inline-flex items-center gap-1.5 text-[11px] font-mono text-cyan-300 hover:text-cyan-200"
          >
            <ExternalLink className="h-3 w-3" />
            codelabs.developers.google.com/cloudnet-agent-gateway
          </a>
        </div>
      </div>

      {/* Request path */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Workflow className="h-4 w-4 text-cyan-400" />
          Request path
        </h4>
        <div className="flex flex-wrap items-center gap-2 font-mono text-[11px]">
          {[
            "ADK agent",
            "Agent Runtime",
            "Agent Gateway",
            "IAP REQUEST_AUTHZ",
            "Model Armor",
            "MCP on Cloud Run",
          ].map((node, idx, arr) => (
            <React.Fragment key={node}>
              <span
                className={`px-2.5 py-1 rounded-lg border ${
                  node === "Agent Gateway"
                    ? "bg-cyan-500/15 text-cyan-200 border-cyan-500/40"
                    : node === "IAP REQUEST_AUTHZ" || node === "Model Armor"
                    ? "bg-rose-500/10 text-rose-300 border-rose-500/40"
                    : "bg-slate-800/70 text-slate-300 border-slate-700/60"
                }`}
              >
                {node}
              </span>
              {idx < arr.length - 1 && (
                <span className="text-slate-600">→</span>
              )}
            </React.Fragment>
          ))}
        </div>
        <p className="text-[11px] text-slate-400 mt-3 leading-relaxed">
          Tool URLs are resolved through the Agent Registry at call time rather
          than baked into the agent image, so both policy and topology change
          without a rebuild.
        </p>
      </div>

      {/* Controls */}
      <div>
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Lock className="h-4 w-4 text-rose-400" />
          Enforcement controls
        </h4>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {data.controls.map((c) => (
            <div
              key={c.id}
              className={`p-4 rounded-2xl bg-slate-900/80 border backdrop-blur-xl ${CONTROL_ACCENT[c.kind]}`}
            >
              <div className="flex items-center gap-2 mb-1">
                {CONTROL_ICON[c.kind]}
                <h5 className="text-sm font-bold font-display text-white tracking-tight">
                  {c.name}
                </h5>
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
                  {c.kind}
                </span>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed">{c.summary}</p>
              <p className="text-[10.5px] font-mono text-slate-500 mt-2">
                enforced at: {c.enforcedAt}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Deployment modes */}
      <div>
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Globe className="h-4 w-4 text-emerald-400" />
          Deployment modes
        </h4>
        <p className="text-[11px] text-slate-400 mb-3 max-w-3xl leading-relaxed">
          Chosen with the <code className="text-cyan-300">enable_cloud_run_private_networking</code>{" "}
          Terraform flag.
        </p>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Mode</th>
                  <th className="px-4 py-2.5">Cloud Run ingress</th>
                  <th className="px-4 py-2.5">Registry URLs</th>
                  <th className="px-4 py-2.5">Extra requirements</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {data.modes.map((m) => (
                  <tr key={m.mode} className="hover:bg-slate-800/40 transition-colors align-top">
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full border text-[10px] uppercase ${
                          m.secure
                            ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/40"
                            : "bg-slate-700/40 text-slate-300 border-slate-600/40"
                        }`}
                      >
                        {m.mode}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-cyan-300">{m.cloudRunIngress}</td>
                    <td className="px-4 py-3">{m.registryUrls}</td>
                    <td className="px-4 py-3 leading-relaxed">{m.extraRequirements}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* MCP services + prerequisites */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
            <Server className="h-4 w-4 text-cyan-400" />
            MCP services behind the gateway
          </h4>
          <ul className="space-y-2">
            {data.mcpServices.map((s) => (
              <li
                key={s.name}
                className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80"
              >
                <code className="text-[12px] font-mono text-cyan-300">{s.name}</code>
                <p className="text-[11px] text-slate-400 mt-0.5">{s.purpose}</p>
              </li>
            ))}
          </ul>
          <p className="text-[10.5px] text-slate-500 mt-3 leading-relaxed">
            Each gets its own Cloud Run runtime service account, which is what
            makes per-tool IAM enforceable.
          </p>
        </div>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
            <Eye className="h-4 w-4 text-amber-400" />
            Prerequisites
          </h4>
          <ul className="space-y-1.5 text-[11px] text-slate-300 leading-relaxed">
            {data.prerequisites.map((p, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <Check className="h-3.5 w-3.5 text-emerald-400 mt-0.5 shrink-0" />
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Deploy sequence */}
      <div className="space-y-3">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
          <Terminal className="h-4 w-4 text-emerald-400" />
          Deploy sequence
        </h4>
        <div className="space-y-2">
          {data.steps.map((s) => (
            <div
              key={s.order}
              className="rounded-xl border border-slate-800/80 bg-slate-950/60 overflow-hidden"
            >
              <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800/80 bg-slate-900/70">
                <div className="flex items-center gap-2.5">
                  <span className="text-[11px] font-mono text-slate-500">
                    {String(s.order).padStart(2, "0")}
                  </span>
                  <span className="text-[12px] font-bold text-white font-display">
                    {s.title}
                  </span>
                </div>
                <CopyButton payload={s.command} />
              </div>
              <pre className="p-3 text-[11px] font-mono text-cyan-300 overflow-x-auto leading-relaxed">
                {s.command}
              </pre>
            </div>
          ))}
        </div>
      </div>

      {/* Relevance to this repo */}
      <div className="glass-panel rounded-2xl border border-cyan-500/30 bg-cyan-500/[0.04] backdrop-blur-xl p-5">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-2">
          <ShieldCheck className="h-4 w-4 text-cyan-400" />
          How this maps onto sakthai
        </h4>
        <p className="text-[11.5px] text-slate-300 leading-relaxed">
          {data.sakthaiRelevance}
        </p>
      </div>
    </div>
  );
}

export default AgentGatewayPanel;
