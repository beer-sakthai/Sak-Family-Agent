"use client";

import React, { useMemo, useState } from "react";
import {
  CheckCircle2,
  FileText,
  Filter,
  GitBranch,
  PenLine,
  Rocket,
  ScrollText,
} from "lucide-react";
import { DesignSpec, DesignSpecsData, SpecStatus } from "@/lib/types";

interface DesignSpecsPanelProps {
  data: DesignSpecsData | null;
}

const STATUS_META: Record<
  SpecStatus,
  { label: string; cls: string; icon: React.ReactNode }
> = {
  approved: {
    label: "approved",
    cls: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  implemented: {
    label: "implemented",
    cls: "bg-cyan-500/15 text-cyan-300 border-cyan-500/40",
    icon: <Rocket className="h-3 w-3" />,
  },
  draft: {
    label: "draft",
    cls: "bg-amber-500/15 text-amber-300 border-amber-500/40",
    icon: <PenLine className="h-3 w-3" />,
  },
  unknown: {
    label: "no status",
    cls: "bg-slate-700/40 text-slate-300 border-slate-600/40",
    icon: <FileText className="h-3 w-3" />,
  },
};

function SpecCard({ spec }: { spec: DesignSpec }) {
  const meta = STATUS_META[spec.status];
  return (
    <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
      <div className="flex items-start justify-between gap-3 mb-1.5">
        <div className="min-w-0">
          <h5 className="text-sm font-bold font-display text-white tracking-tight">
            {spec.title}
          </h5>
          <code className="text-[10.5px] font-mono text-slate-500 break-all">
            {spec.file}
          </code>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <span
            className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-full border inline-flex items-center gap-1 ${meta.cls}`}
          >
            {meta.icon}
            {meta.label}
          </span>
          {spec.date && (
            <span className="text-[10px] font-mono text-slate-500">{spec.date}</span>
          )}
        </div>
      </div>

      {spec.summary && (
        <p className="text-[11.5px] text-slate-300 leading-relaxed mt-2">
          {spec.summary}
        </p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-1.5 font-mono text-[10px]">
        {spec.planFile && (
          <span className="px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/40 inline-flex items-center gap-1">
            <GitBranch className="h-3 w-3" />
            has plan
          </span>
        )}
        {spec.relatedTab && (
          <span className="px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/40">
            → {spec.relatedTab}
          </span>
        )}
        <span className="px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400 border border-slate-700/60">
          {(spec.bytes / 1024).toFixed(1)} KB
        </span>
      </div>

      {spec.statusRaw && spec.statusRaw !== "(no status line)" && (
        <p className="text-[10.5px] font-mono text-slate-500 mt-2 leading-relaxed">
          {spec.statusRaw}
        </p>
      )}
    </div>
  );
}

export function DesignSpecsPanel({ data }: DesignSpecsPanelProps) {
  const [status, setStatus] = useState<SpecStatus | "all">("all");

  const filtered = useMemo(() => {
    if (!data) return [];
    if (status === "all") return data.specs;
    return data.specs.filter((s) => s.status === status);
  }, [data, status]);

  if (!data || !data.present) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <ScrollText className="h-5 w-5 text-cyan-400" />
            Design Specs
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            No specs directory found. Expected{" "}
            <code className="text-cyan-300">docs/superpowers/specs/</code> at the
            repo root, or set <code className="text-cyan-300">SAK_REPO_ROOT</code>.
          </p>
        </div>
      </div>
    );
  }

  const counts: Record<string, number> = { all: data.specs.length };
  for (const s of data.specs) {
    counts[s.status] = (counts[s.status] ?? 0) + 1;
  }
  const statusKeys: Array<SpecStatus | "all"> = [
    "all",
    "approved",
    "draft",
    "implemented",
    "unknown",
  ];

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
          <ScrollText className="h-5 w-5 text-cyan-400" />
          Design Specs
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60">
            {data.specs.length}
          </span>
        </h3>
        <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
          The repo&apos;s own design record, read live from{" "}
          <code className="text-cyan-300">{data.specsDir}</code>. Each spec is a
          brainstormed decision log — status, scope, non-goals, and the
          reasoning behind the choices — paired with an implementation plan in{" "}
          <code className="text-cyan-300">{data.plansDir}</code> where one
          exists. Status is parsed from each file&apos;s own{" "}
          <code className="text-cyan-300">**Status:**</code> line, so this view
          can&apos;t drift from the documents.
        </p>
      </div>

      {/* Filter */}
      <div className="flex flex-wrap items-center gap-1.5 font-mono text-[11px]">
        <span className="text-slate-500 pr-1 flex items-center gap-1">
          <Filter className="h-3 w-3 text-cyan-400" /> Status:
        </span>
        {statusKeys
          .filter((k) => k === "all" || (counts[k] ?? 0) > 0)
          .map((k) => (
            <button
              key={k}
              onClick={() => setStatus(k)}
              className={`px-2.5 py-1 rounded-lg border transition-colors ${
                status === k
                  ? "bg-cyan-500/15 text-cyan-200 border-cyan-500/40"
                  : "bg-slate-800/60 text-slate-400 border-slate-700/60 hover:text-slate-200"
              }`}
            >
              {k === "all" ? "All" : STATUS_META[k].label} ({counts[k] ?? 0})
            </button>
          ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filtered.map((s) => (
          <SpecCard key={s.id} spec={s} />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 p-10 text-center text-slate-500 italic">
          No specs match this status filter.
        </div>
      )}
    </div>
  );
}

export default DesignSpecsPanel;
