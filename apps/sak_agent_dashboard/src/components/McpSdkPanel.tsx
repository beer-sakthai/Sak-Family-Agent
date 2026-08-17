"use client";

import React, { useState } from "react";
import {
  Boxes,
  BookOpen,
  Check,
  Copy,
  ExternalLink,
  FileCode,
  Folder,
  GitBranch,
  Package,
  Radio,
  Server,
  Wrench,
  Zap,
} from "lucide-react";
import {
  McpSdkData,
  SdkPrimitive,
  SdkPrimitiveKind,
  SdkScaffoldFile,
} from "@/lib/types";

interface McpSdkPanelProps {
  data: McpSdkData | null;
}

const KIND_ICON: Record<SdkPrimitiveKind, React.ReactNode> = {
  server: <Server className="h-3.5 w-3.5 text-cyan-300" />,
  tool: <Wrench className="h-3.5 w-3.5 text-emerald-300" />,
  resource: <BookOpen className="h-3.5 w-3.5 text-purple-300" />,
  prompt: <FileCode className="h-3.5 w-3.5 text-amber-300" />,
  transport: <Radio className="h-3.5 w-3.5 text-sky-300" />,
  client: <Boxes className="h-3.5 w-3.5 text-rose-300" />,
  context: <Zap className="h-3.5 w-3.5 text-slate-300" />,
};

const KIND_ACCENT: Record<SdkPrimitiveKind, string> = {
  server: "text-cyan-300 border-cyan-500/40 bg-cyan-500/10",
  tool: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10",
  resource: "text-purple-300 border-purple-500/40 bg-purple-500/10",
  prompt: "text-amber-300 border-amber-500/40 bg-amber-500/10",
  transport: "text-sky-300 border-sky-500/40 bg-sky-500/10",
  client: "text-rose-300 border-rose-500/40 bg-rose-500/10",
  context: "text-slate-300 border-slate-600/50 bg-slate-500/10",
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
      aria-label="Copy snippet"
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

function PrimitiveCard({ primitive }: { primitive: SdkPrimitive }) {
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
        <div className="flex items-center gap-2">
          <a
            href={primitive.docsUrl}
            target="_blank"
            rel="noreferrer noopener"
            className="text-[11px] font-mono text-cyan-300 hover:text-cyan-200 inline-flex items-center gap-1"
          >
            <ExternalLink className="h-3 w-3" /> Docs
          </a>
          <CopyButton payload={primitive.snippet} />
        </div>
      </div>
      <pre className="p-4 text-[11px] font-mono text-slate-200 bg-slate-950/80 overflow-x-auto leading-relaxed">
        {primitive.snippet}
      </pre>
    </div>
  );
}

function ScaffoldFileTile({ file }: { file: SdkScaffoldFile }) {
  const [open, setOpen] = useState(false);
  const icon =
    file.language === "python"
      ? <FileCode className="h-3.5 w-3.5 text-amber-300" />
      : file.language === "toml"
      ? <Package className="h-3.5 w-3.5 text-emerald-300" />
      : file.language === "json"
      ? <Boxes className="h-3.5 w-3.5 text-sky-300" />
      : <BookOpen className="h-3.5 w-3.5 text-purple-300" />;
  return (
    <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 overflow-hidden">
      <div
        onClick={() => setOpen((v) => !v)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setOpen((v) => !v);
          }
        }}
        role="button"
        tabIndex={0}
        aria-expanded={open}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-900/50 transition-colors text-left cursor-pointer select-none"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          {icon}
          <div className="min-w-0">
            <code className="text-[12px] font-mono text-white font-semibold truncate block">
              {file.path}
            </code>
            <div className="text-[10.5px] font-mono text-slate-500 mt-0.5 uppercase">
              {file.language}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <CopyButton payload={file.content} />
          <span
            className="text-slate-500 cursor-pointer p-1"
            onClick={(e) => {
              e.stopPropagation();
              setOpen((v) => !v);
            }}
          >
            {open ? "▾" : "▸"}
          </span>
        </div>
      </div>
      {open && (
        <pre className="p-4 text-[11px] font-mono text-slate-200 bg-slate-950/80 border-t border-slate-800/80 overflow-x-auto leading-relaxed whitespace-pre">
          {file.content}
        </pre>
      )}
    </div>
  );
}

export function McpSdkPanel({ data }: McpSdkPanelProps) {
  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Boxes className="h-5 w-5 text-cyan-400" />
            MCP SDK
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Loading SDK inventory…
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
            <Boxes className="h-5 w-5 text-cyan-400" />
            {data.overview.title}
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60">
              protocol {data.overview.protocolVersion}
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5 max-w-3xl leading-relaxed">
            {data.overview.description}
          </p>
          <a
            href={data.overview.docsUrl}
            target="_blank"
            rel="noreferrer noopener"
            className="mt-1.5 inline-flex items-center gap-1.5 text-[11px] font-mono text-cyan-300 hover:text-cyan-200"
          >
            <GitBranch className="h-3.5 w-3.5" />
            modelcontextprotocol/python-sdk
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>

      {/* Packages */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.packages.map((pkg) => (
          <div
            key={pkg.name}
            className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5"
          >
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex items-start gap-2.5">
                <div className="p-2 rounded-lg bg-gradient-to-br from-cyan-500/30 to-blue-600/30 border border-cyan-500/30">
                  <Package className="h-4 w-4 text-cyan-300" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <code className="text-[13px] font-mono text-white font-bold">
                      {pkg.name}
                    </code>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
                      {pkg.license}
                    </span>
                    {pkg.detectedVersionSpec && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                        pinned {pkg.detectedVersionSpec}
                      </span>
                    )}
                  </div>
                  <p className="text-[10.5px] font-mono text-slate-500 mt-0.5">
                    {pkg.displayName}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <a
                  href={pkg.repoUrl}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="text-[10px] font-mono text-cyan-300 hover:text-cyan-200 inline-flex items-center gap-1 px-2 py-0.5 rounded border border-slate-700/60 bg-slate-800/60"
                >
                  <GitBranch className="h-3 w-3" /> repo
                </a>
                <a
                  href={pkg.pypi}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="text-[10px] font-mono text-cyan-300 hover:text-cyan-200 inline-flex items-center gap-1 px-2 py-0.5 rounded border border-slate-700/60 bg-slate-800/60"
                >
                  <ExternalLink className="h-3 w-3" /> pypi
                </a>
              </div>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">{pkg.role}</p>
            <div className="mt-3 rounded-lg border border-slate-800/80 bg-slate-950/80 overflow-hidden">
              <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800/80 bg-slate-900/70">
                <span className="text-[10px] font-mono text-slate-400 uppercase">
                  install
                </span>
                <CopyButton payload={pkg.installCommand} />
              </div>
              <pre className="p-3 text-[11px] font-mono text-cyan-300 overflow-x-auto">
                {pkg.installCommand}
              </pre>
            </div>
            <p className="text-[11px] font-mono text-slate-400 mt-3 leading-relaxed">
              <span className="text-slate-500 uppercase text-[10px] mr-1.5">
                in-repo
              </span>
              {pkg.usedInRepoAs}
            </p>
          </div>
        ))}
      </div>

      {/* Primitives */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Wrench className="h-4 w-4 text-emerald-400" />
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

      {/* In-repo usage */}
      <div className="space-y-3">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-cyan-400" />
          Where this SDK meets the repo
        </h4>
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 overflow-hidden">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-4 py-2.5">Kind</th>
                <th className="px-4 py-2.5">Path</th>
                <th className="px-4 py-2.5">Detail</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {data.usageSites.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-slate-500 italic">
                    No SDK usage sites detected in the repo.
                  </td>
                </tr>
              ) : (
                data.usageSites.map((s) => (
                  <tr key={s.path} className="hover:bg-slate-800/40 transition-colors align-top">
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded border text-[10px] uppercase ${
                          s.kind === "pyproject"
                            ? "text-emerald-300 border-emerald-500/40 bg-emerald-500/10"
                            : s.kind === "import"
                            ? "text-cyan-300 border-cyan-500/40 bg-cyan-500/10"
                            : "text-amber-300 border-amber-500/40 bg-amber-500/10"
                        }`}
                      >
                        {s.kind === "custom-implementation" ? "custom" : s.kind}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-cyan-300 whitespace-nowrap">{s.path}</td>
                    <td className="px-4 py-3 text-slate-300 leading-relaxed max-w-2xl">
                      {s.detail}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Scaffold */}
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2">
              <Folder className="h-4 w-4 text-amber-400" />
              Scaffold: new MCP server (services/{data.scaffold.name}/)
            </h4>
            <p className="text-[11px] text-slate-400 mt-1 max-w-3xl leading-relaxed">
              {data.scaffold.description}
            </p>
          </div>
        </div>
        <div className="space-y-2">
          {data.scaffold.files.map((f) => (
            <ScaffoldFileTile key={f.path} file={f} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default McpSdkPanel;
