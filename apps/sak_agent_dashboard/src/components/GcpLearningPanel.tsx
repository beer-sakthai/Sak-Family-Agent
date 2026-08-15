"use client";

import React, { useMemo, useState } from "react";
import {
  AlertTriangle,
  ExternalLink,
  Filter,
  GraduationCap,
  Folder,
  BookOpen,
  GitBranch,
} from "lucide-react";
import { GithubIcon as Github } from "./GithubIcon";
import { GCP_LEARNING_STALENESS_NOTES } from "@/lib/gcpLearning";
import {
  GcpLearningData,
  GcpLearningResource,
  GcpLearningTag,
} from "@/lib/types";

interface GcpLearningPanelProps {
  data: GcpLearningData | null;
}

const TAG_ACCENT: Record<GcpLearningTag, string> = {
  agents: "text-cyan-300 border-cyan-500/40 bg-cyan-500/10",
  ml: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10",
  data: "text-sky-300 border-sky-500/40 bg-sky-500/10",
  notebooks: "text-amber-300 border-amber-500/40 bg-amber-500/10",
  labs: "text-purple-300 border-purple-500/40 bg-purple-500/10",
  docs: "text-slate-300 border-slate-600/50 bg-slate-500/10",
};

function ResourceCard({
  resource,
  labels,
}: {
  resource: GcpLearningResource;
  labels: Record<GcpLearningTag, string>;
}) {
  return (
    <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl">
      <div className="flex items-start justify-between gap-3 mb-1">
        <div className="flex items-start gap-2.5 min-w-0">
          <Folder className="h-4 w-4 text-amber-400 mt-1 shrink-0" />
          <div className="min-w-0">
            <h5 className="text-sm font-bold font-display text-white tracking-tight">
              {resource.title}
            </h5>
            <code className="text-[11px] font-mono text-cyan-300 break-all">
              {resource.path}
            </code>
          </div>
        </div>
        <a
          href={resource.url}
          target="_blank"
          rel="noreferrer noopener"
          className="text-[10px] font-mono text-cyan-300 hover:text-cyan-200 inline-flex items-center gap-1 px-2 py-0.5 rounded border border-slate-700/60 bg-slate-800/60 shrink-0"
        >
          open <ExternalLink className="h-3 w-3" />
        </a>
      </div>
      <p className="text-[11px] text-slate-300 leading-relaxed mt-1">
        {resource.description}
      </p>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {resource.tags.map((t) => (
          <span
            key={t}
            className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-full border ${TAG_ACCENT[t]}`}
          >
            {labels[t]}
          </span>
        ))}
      </div>
    </div>
  );
}

export function GcpLearningPanel({ data }: GcpLearningPanelProps) {
  const [tag, setTag] = useState<GcpLearningTag | "all">("all");

  const filtered = useMemo(() => {
    if (!data) return [];
    if (tag === "all") return data.resources;
    return data.resources.filter((r) => r.tags.includes(tag));
  }, [data, tag]);

  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <GraduationCap className="h-5 w-5 text-cyan-400" />
            GCP Learning
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Loading learning inventory…</p>
        </div>
      </div>
    );
  }

  const tagKeys: Array<GcpLearningTag | "all"> = [
    "all",
    ...(Object.keys(data.tagLabels) as GcpLearningTag[]),
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <GraduationCap className="h-5 w-5 text-cyan-400" />
            {data.overview.title}
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60">
              {data.overview.stars}
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
              {data.overview.license}
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
            GoogleCloudPlatform/training-data-analyst
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap items-center gap-1.5 font-mono text-[11px]">
        <span className="text-slate-500 pr-1 flex items-center gap-1">
          <Filter className="h-3 w-3 text-cyan-400" /> Tag:
        </span>
        {tagKeys.map((k) => (
          <button
            key={k}
            onClick={() => setTag(k)}
            className={`px-2.5 py-1 rounded-lg border transition-colors ${
              tag === k
                ? "bg-cyan-500/15 text-cyan-200 border-cyan-500/40"
                : "bg-slate-800/60 text-slate-400 border-slate-700/60 hover:text-slate-200"
            }`}
          >
            {k === "all" ? "All" : data.tagLabels[k]}
          </button>
        ))}
      </div>

      {/* Resources */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {filtered.map((r) => (
          <ResourceCard key={r.id} resource={r} labels={data.tagLabels} />
        ))}
      </div>

      {/* Staleness warning */}
      <div className="glass-panel rounded-2xl border border-amber-500/30 bg-amber-500/[0.04] backdrop-blur-xl p-5">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-2">
          <AlertTriangle className="h-4 w-4 text-amber-400" />
          Read for shape, not for commands
        </h4>
        <p className="text-[11px] text-slate-400 mb-3 leading-relaxed max-w-3xl">
          Large parts of this repo predate Vertex AI. The workflows still teach
          the right arc; the exact CLI invocations often target retired
          surfaces.
        </p>
        <ul className="space-y-1.5 text-[11px] text-slate-300 leading-relaxed">
          {GCP_LEARNING_STALENESS_NOTES.map((n, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-amber-400 mt-0.5">•</span>
              <span>{n}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Note */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-5">
        <h4 className="text-sm font-bold font-display text-white tracking-tight flex items-center gap-2 mb-2">
          <BookOpen className="h-4 w-4 text-fuchsia-400" />
          Why this is only a linking tab
        </h4>
        <p className="text-[11.5px] text-slate-300 leading-relaxed">
          training-data-analyst is ~8k commits deep with per-course sub-trees
          that Google updates independently. Copying notebooks into this repo
          would rot fast and confuse ownership. This tab is a curated jumping-off
          list — filtered by what&apos;s relevant to the personas — and links out to
          the live directories so you always see current material.
        </p>
      </div>
    </div>
  );
}

export default GcpLearningPanel;
