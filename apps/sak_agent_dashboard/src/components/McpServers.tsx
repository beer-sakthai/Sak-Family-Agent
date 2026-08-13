"use client";

import React, { useMemo, useState } from "react";
import {
  Plug,
  Server,
  Search,
  Copy,
  Check,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  KeyRound,
  Wrench,
  Filter,
  BookOpen,
  Zap,
} from "lucide-react";
import {
  McpAction,
  McpActionCategory,
  McpActionStability,
  McpServerSpec,
} from "@/lib/types";

interface McpServersProps {
  servers: McpServerSpec[];
}

const CATEGORY_LABELS: Record<McpActionCategory | "all", string> = {
  all: "All",
  teams: "Teams & Channels",
  chats: "Chats",
  meetings: "Meetings",
  calendar: "Calendar",
  users: "Users & Presence",
  copilot: "Copilot",
  other: "Other",
};

const CATEGORY_ACCENTS: Record<McpActionCategory, string> = {
  teams: "text-cyan-300 border-cyan-500/40 bg-cyan-500/10",
  chats: "text-sky-300 border-sky-500/40 bg-sky-500/10",
  meetings: "text-purple-300 border-purple-500/40 bg-purple-500/10",
  calendar: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10",
  users: "text-amber-300 border-amber-500/40 bg-amber-500/10",
  copilot: "text-rose-300 border-rose-500/40 bg-rose-500/10",
  other: "text-slate-300 border-slate-600/50 bg-slate-500/10",
};

const METHOD_ACCENTS: Record<string, string> = {
  GET: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10",
  POST: "text-sky-300 border-sky-500/40 bg-sky-500/10",
  PATCH: "text-amber-300 border-amber-500/40 bg-amber-500/10",
  DELETE: "text-rose-300 border-rose-500/40 bg-rose-500/10",
  PUT: "text-purple-300 border-purple-500/40 bg-purple-500/10",
};

function StabilityBadge({ stability }: { stability: McpActionStability }) {
  if (stability === "stable") {
    return (
      <span className="px-2 py-0.5 rounded-full font-mono text-[10px] uppercase font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
        stable
      </span>
    );
  }
  if (stability === "beta") {
    return (
      <span className="px-2 py-0.5 rounded-full font-mono text-[10px] uppercase font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
        beta
      </span>
    );
  }
  return (
    <span className="px-2 py-0.5 rounded-full font-mono text-[10px] uppercase font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1 w-fit">
      <AlertTriangle className="h-3 w-3" />
      verify
    </span>
  );
}

function StatusPulse({ server }: { server: McpServerSpec }) {
  const map = {
    healthy: {
      cls: "bg-emerald-500/10 text-emerald-300 border-emerald-500/40",
      dot: "bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]",
      label: "Healthy",
    },
    degraded: {
      cls: "bg-amber-500/10 text-amber-300 border-amber-500/40",
      dot: "bg-amber-400 animate-pulse",
      label: "Degraded",
    },
    unconfigured: {
      cls: "bg-slate-800/80 text-slate-400 border-slate-700",
      dot: "bg-slate-500",
      label: "Not Configured",
    },
    unknown: {
      cls: "bg-slate-800/80 text-slate-400 border-slate-700",
      dot: "bg-slate-500",
      label: "Unknown",
    },
  } as const;
  const s = map[server.status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold font-mono border ${s.cls}`}
    >
      <span className={`h-2 w-2 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
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
      aria-label="Copy configuration"
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

function ServerCard({ server }: { server: McpServerSpec }) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<McpActionCategory | "all">("all");
  const [showDelegatedOnly, setShowDelegatedOnly] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState(0);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return server.actions.filter((a: McpAction) => {
      if (category !== "all" && a.category !== category) return false;
      if (showDelegatedOnly && !a.requiresDelegatedAuth) return false;
      if (q.length === 0) return true;
      return (
        a.id.toLowerCase().includes(q) ||
        a.description.toLowerCase().includes(q) ||
        a.pathTemplate.toLowerCase().includes(q) ||
        a.method.toLowerCase().includes(q)
      );
    });
  }, [server.actions, query, category, showDelegatedOnly]);

  const stableCount = server.actions.filter((a) => a.stability === "stable").length;
  const verifyCount = server.actions.filter((a) => a.stability === "verify").length;
  const delegatedCount = server.actions.filter((a) => a.requiresDelegatedAuth).length;
  const activeTarget = server.registrationTargets[selectedTarget] ?? server.registrationTargets[0];
  const hasActions = server.actions.length > 0;
  const hasEnvVars = server.envVars.length > 0;
  const disabledToolCount = server.tools.filter((t) => t.disabled).length;

  return (
    <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl shadow-xl overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-slate-800/70 flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-cyan-500/30 to-blue-600/30 border border-cyan-500/30 shadow-lg shadow-cyan-950/40">
            <Server className="h-6 w-6 text-cyan-300" />
          </div>
          <div>
            <h3 className="text-lg font-bold font-display text-white tracking-tight flex items-center gap-2">
              {server.displayName}
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
                {server.transport}
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed max-w-2xl">
              {server.description}
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5 font-mono text-[10px]">
              <span className="px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/60">
                {server.category}
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/60">
                {server.language}
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/60">
                entry: {server.entrypoint}
              </span>
            </div>
          </div>
        </div>
        <div className="flex flex-col items-start md:items-end gap-2">
          <StatusPulse server={server} />
          {server.docsUrl && (
            <a
              href={server.docsUrl}
              target="_blank"
              rel="noreferrer noopener"
              className="text-[11px] font-mono text-cyan-300 hover:text-cyan-200 inline-flex items-center gap-1.5"
            >
              <ExternalLink className="h-3 w-3" />
              Source
            </a>
          )}
        </div>
      </div>

      {/* Status reason banner */}
      <div
        className={`px-5 py-2.5 text-xs font-mono border-b border-slate-800/70 ${
          server.status === "healthy"
            ? "text-emerald-300 bg-emerald-500/5"
            : server.status === "degraded"
            ? "text-amber-300 bg-amber-500/5"
            : "text-slate-400 bg-slate-950/50"
        }`}
      >
        {server.status === "healthy" ? (
          <ShieldCheck className="h-3.5 w-3.5 inline mr-2" />
        ) : (
          <ShieldAlert className="h-3.5 w-3.5 inline mr-2" />
        )}
        {server.statusReason}
      </div>

      {/* Stat tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-5 bg-slate-950/40 border-b border-slate-800/70">
        {hasActions ? (
          <>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                Actions
              </div>
              <div className="text-2xl font-extrabold text-white font-display">
                {server.actions.length}
              </div>
              <div className="text-[10px] font-mono text-slate-500">catalog entries</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                Stable
              </div>
              <div className="text-2xl font-extrabold text-emerald-300 font-display">
                {stableCount}
              </div>
              <div className="text-[10px] font-mono text-slate-500">production-ready</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                Verify
              </div>
              <div className="text-2xl font-extrabold text-rose-300 font-display">
                {verifyCount}
              </div>
              <div className="text-[10px] font-mono text-slate-500">re-check upstream</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                Delegated-only
              </div>
              <div className="text-2xl font-extrabold text-amber-300 font-display">
                {delegatedCount}
              </div>
              <div className="text-[10px] font-mono text-slate-500">
                unsupported in app-only auth
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                MCP tools
              </div>
              <div className="text-2xl font-extrabold text-white font-display">
                {server.tools.length}
              </div>
              <div className="text-[10px] font-mono text-slate-500">exposed to agents</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                Transport
              </div>
              <div className="text-2xl font-extrabold text-cyan-300 font-display uppercase">
                {server.transport}
              </div>
              <div className="text-[10px] font-mono text-slate-500">wire protocol</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                Local env
              </div>
              <div className="text-2xl font-extrabold text-emerald-300 font-display">
                {hasEnvVars ? server.envVars.length : "0"}
              </div>
              <div className="text-[10px] font-mono text-slate-500">
                {hasEnvVars ? "vars required" : "hosted service"}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                Disabled tools
              </div>
              <div className="text-2xl font-extrabold text-rose-300 font-display">
                {disabledToolCount}
              </div>
              <div className="text-[10px] font-mono text-slate-500">not currently usable</div>
            </div>
          </>
        )}
      </div>

      {/* Env & Tools */}
      <div
        className={`grid grid-cols-1 ${
          hasEnvVars ? "lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x" : ""
        } gap-0 divide-slate-800/70`}
      >
        {/* Env vars */}
        {hasEnvVars && (
          <div className="p-5">
            <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-2 mb-3">
              <KeyRound className="h-3.5 w-3.5 text-amber-400" />
              Required environment
            </h4>
            <ul className="space-y-2">
              {server.envVars.map((env) => (
                <li
                  key={env.key}
                  className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80"
                >
                  <div className="flex items-center justify-between mb-1">
                    <code className="text-[12px] font-mono text-cyan-300">{env.key}</code>
                    {env.required ? (
                      <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40">
                        required
                      </span>
                    ) : (
                      <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-700/40 text-slate-300 border border-slate-600/40">
                        optional
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{env.purpose}</p>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Dedicated tool shortcuts */}
        <div className="p-5">
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-2 mb-3">
            <Wrench className="h-3.5 w-3.5 text-emerald-400" />
            Dedicated MCP tools
          </h4>
          <ul className="space-y-2">
            {server.tools.map((tool) => (
              <li
                key={tool.name}
                className={`p-3 rounded-lg border ${
                  tool.disabled
                    ? "bg-rose-500/5 border-rose-500/30"
                    : "bg-slate-950/60 border-slate-800/80"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <code className="text-[12px] font-mono text-white font-semibold">
                    {tool.name}
                  </code>
                  {tool.disabled && (
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3" />
                      not usable
                    </span>
                  )}
                </div>
                <code className="text-[10.5px] font-mono text-slate-400 block mb-1 break-all">
                  {tool.signature}
                </code>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  {tool.description}
                </p>
                {tool.disabled && tool.disabledReason && (
                  <p className="text-[11px] mt-1.5 text-rose-300 leading-relaxed">
                    {tool.disabledReason}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Action catalog */}
      {hasActions && (
      <div className="p-5 border-t border-slate-800/70">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
          <div>
            <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
              <Zap className="h-4 w-4 text-cyan-400" />
              Graph action catalog
            </h4>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Curated Microsoft Graph endpoints, callable via <code className="text-cyan-300">execute_action(id, …)</code>. Anything not listed is still reachable via <code className="text-cyan-300">execute_raw</code>.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="h-3.5 w-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search actions…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs font-mono bg-slate-950/80 border border-slate-800/80 rounded-lg text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50 w-56"
              />
            </div>
            <button
              onClick={() => setShowDelegatedOnly((v) => !v)}
              className={`text-[11px] font-mono px-2.5 py-1.5 rounded-lg border transition-colors ${
                showDelegatedOnly
                  ? "bg-amber-500/20 text-amber-200 border-amber-500/40"
                  : "bg-slate-800/70 text-slate-400 border-slate-700/60 hover:text-slate-200"
              }`}
              title="Show only actions that require delegated (signed-in) auth"
            >
              Delegated-only
            </button>
          </div>
        </div>

        {/* Category filter chips */}
        <div className="flex flex-wrap items-center gap-1.5 mb-4 font-mono text-[11px]">
          <span className="text-slate-500 pr-1 flex items-center gap-1">
            <Filter className="h-3 w-3 text-cyan-400" /> Category:
          </span>
          {(Object.keys(CATEGORY_LABELS) as Array<McpActionCategory | "all">).map((k) => (
            <button
              key={k}
              onClick={() => setCategory(k)}
              className={`px-2.5 py-1 rounded-lg border transition-colors ${
                category === k
                  ? "bg-cyan-500/15 text-cyan-200 border-cyan-500/40"
                  : "bg-slate-800/60 text-slate-400 border-slate-700/60 hover:text-slate-200"
              }`}
            >
              {CATEGORY_LABELS[k]}
            </button>
          ))}
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800/70">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-4 py-2.5">Method</th>
                <th className="px-4 py-2.5">Action</th>
                <th className="px-4 py-2.5">Path</th>
                <th className="px-4 py-2.5">Category</th>
                <th className="px-4 py-2.5">Stability</th>
                <th className="px-4 py-2.5">Auth</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500 italic">
                    No catalog actions match the current filters.
                  </td>
                </tr>
              ) : (
                filtered.map((a) => (
                  <tr
                    key={a.id}
                    className="hover:bg-slate-800/40 transition-colors align-top"
                  >
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded font-bold text-[10px] uppercase border ${
                          METHOD_ACCENTS[a.method] ??
                          "text-slate-300 border-slate-600/50 bg-slate-500/10"
                        }`}
                      >
                        {a.method}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-bold text-white">{a.id}</div>
                      <div className="text-[10.5px] text-slate-400 leading-relaxed max-w-md">
                        {a.description}
                      </div>
                      {a.params.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {a.params.map((p) => (
                            <span
                              key={p}
                              className="px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700/60 text-[10px] text-slate-300"
                            >
                              {p}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-cyan-300 whitespace-nowrap">
                      {a.pathTemplate}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full border text-[10px] uppercase ${CATEGORY_ACCENTS[a.category]}`}
                      >
                        {a.category}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <StabilityBadge stability={a.stability} />
                    </td>
                    <td className="px-4 py-3">
                      {a.requiresDelegatedAuth ? (
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 whitespace-nowrap">
                          delegated
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 whitespace-nowrap">
                          app-only
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="mt-2 text-[10.5px] font-mono text-slate-500">
          Showing {filtered.length} of {server.actions.length} actions.
        </div>
      </div>
      )}

      {/* Registration snippets */}
      <div className="p-5 border-t border-slate-800/70">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
          <Plug className="h-4 w-4 text-emerald-400" />
          Register this server
        </h4>
        <div className="flex flex-wrap items-center gap-1.5 mb-3 font-mono text-[11px]">
          {server.registrationTargets.map((t, i) => (
            <button
              key={t.label}
              onClick={() => setSelectedTarget(i)}
              className={`px-2.5 py-1 rounded-lg border transition-colors ${
                selectedTarget === i
                  ? "bg-emerald-500/15 text-emerald-200 border-emerald-500/40"
                  : "bg-slate-800/60 text-slate-400 border-slate-700/60 hover:text-slate-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        {activeTarget && (
          <div className="rounded-xl border border-slate-800/80 bg-slate-950/80 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800/80 bg-slate-900/70">
              <div className="text-[11px] font-mono text-slate-400">
                <code className="text-cyan-300">{activeTarget.path}</code>
                <span className="mx-2 text-slate-600">·</span>
                {activeTarget.format}
              </div>
              <CopyButton payload={activeTarget.snippet} />
            </div>
            <pre className="p-4 text-[11px] font-mono text-slate-200 overflow-x-auto leading-relaxed">
              {activeTarget.snippet}
            </pre>
          </div>
        )}
      </div>

      {/* Known limitations */}
      {server.knownLimitations.length > 0 && (
        <div className="p-5 border-t border-slate-800/70 bg-rose-500/[0.03]">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-3">
            <BookOpen className="h-4 w-4 text-rose-400" />
            Known limitations
          </h4>
          <ul className="space-y-2 text-[11px] text-slate-300 leading-relaxed">
            {server.knownLimitations.map((l, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <AlertTriangle className="h-3.5 w-3.5 text-rose-400 mt-0.5 shrink-0" />
                <span>{l}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function McpServers({ servers }: McpServersProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Plug className="h-5 w-5 text-cyan-400" />
            MCP Servers ({servers.length})
          </h3>
          <p className="text-xs text-slate-400 mt-0.5 max-w-3xl leading-relaxed">
            Registered outbound Model Context Protocol servers. Each server exposes its own tool
            surface to <code className="text-cyan-300">sakthai run</code> / <code className="text-cyan-300">sakthai chat</code>,
            namespaced as <code className="text-cyan-300">&lt;server&gt;__&lt;tool&gt;</code>. This panel is a live
            inventory: catalog, credential state, and copy-paste registration snippets per persona.
          </p>
        </div>
      </div>

      {servers.length === 0 ? (
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 p-10 text-center text-slate-500 italic">
          No MCP servers registered yet.
        </div>
      ) : (
        <div className="space-y-6">
          {servers.map((s) => (
            <ServerCard key={s.id} server={s} />
          ))}
        </div>
      )}
    </div>
  );
}

export default McpServers;
