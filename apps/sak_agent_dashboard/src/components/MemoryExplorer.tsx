"use client";

import React, { useState } from "react";
import { BookOpen, Database, Layers, Lightbulb } from "lucide-react";

import type { MemoryPayload } from "@/lib/contracts.generated";

interface MemoryExplorerProps {
  memory: MemoryPayload;
}

function timestamp(epochSeconds: number): string {
  if (!epochSeconds) return "—";
  return new Date(epochSeconds * 1000).toISOString().replace("T", " ").slice(0, 16);
}

export function MemoryExplorer({ memory }: MemoryExplorerProps) {
  const [activeTab, setActiveTab] = useState<"facts" | "observations">("facts");

  const facts = memory.facts;
  const observations = memory.observations;

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Database className="h-5 w-5 text-emerald-400" />
            Memory Store Explorer
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Facts and observations merged across every persona&apos;s{" "}
            <code className="text-slate-300">memory.db</code> shard
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-cyan-400">
            {memory.total_facts.toLocaleString()} facts
            {memory.facts_this_week > 0 && (
              <span className="text-emerald-400"> (+{memory.facts_this_week} this week)</span>
            )}
          </span>
          <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-violet-400">
            {memory.total_observations.toLocaleString()} observations
          </span>
        </div>
      </div>

      <div role="tablist" className="flex items-center gap-2">
        <button
          role="tab"
          aria-selected={activeTab === "facts"}
          onClick={() => setActiveTab("facts")}
          className={`px-4 py-2 rounded-xl text-xs font-mono border transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
            activeTab === "facts"
              ? "bg-cyan-950/50 text-cyan-300 border-cyan-700/50"
              : "bg-slate-900/60 text-slate-400 border-slate-800 hover:border-slate-700"
          }`}
        >
          <BookOpen className="h-3.5 w-3.5 inline mr-1.5" />
          Facts ({facts.length})
        </button>
        <button
          role="tab"
          aria-selected={activeTab === "observations"}
          onClick={() => setActiveTab("observations")}
          className={`px-4 py-2 rounded-xl text-xs font-mono border transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
            activeTab === "observations"
              ? "bg-violet-950/50 text-violet-300 border-violet-700/50"
              : "bg-slate-900/60 text-slate-400 border-slate-800 hover:border-slate-700"
          }`}
        >
          <Lightbulb className="h-3.5 w-3.5 inline mr-1.5" />
          Observations ({observations.length})
        </button>
      </div>

      {activeTab === "facts" && (
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-5 py-3">ID</th>
                  <th className="px-5 py-3">Kind / Key</th>
                  <th className="px-5 py-3">Value</th>
                  <th className="px-5 py-3">Shard</th>
                  <th className="px-5 py-3 text-right">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {facts.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-8 text-center text-slate-500 italic">
                      No memory facts found.
                    </td>
                  </tr>
                ) : (
                  facts.map((f) => (
                    <tr key={`${f.persona}-${f.id}`} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-5 py-3.5 text-slate-500">{f.id}</td>
                      <td className="px-5 py-3.5 font-bold text-cyan-300">
                        {f.kind}
                        {f.key && <span className="text-slate-500 font-normal"> / {f.key}</span>}
                      </td>
                      <td className="px-5 py-3.5 font-sans text-xs text-slate-200 leading-relaxed">
                        {f.value}
                        {f.tags.length > 0 && (
                          <span className="ml-2 text-[10px] font-mono text-slate-500">
                            {f.tags.map((t) => `#${t}`).join(" ")}
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-emerald-400 border border-emerald-500/20 text-[11px]">
                          {f.persona}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right text-slate-500 text-[11px]">
                        {timestamp(f.updated_at)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "observations" && (
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-5 py-3">ID</th>
                  <th className="px-5 py-3">Shard</th>
                  <th className="px-5 py-3">Observation</th>
                  <th className="px-5 py-3 text-right">Weight</th>
                  <th className="px-5 py-3 text-right">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {observations.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-8 text-center text-slate-500 italic">
                      No observations recorded.
                    </td>
                  </tr>
                ) : (
                  observations.map((o) => (
                    <tr key={`${o.persona}-${o.id}`} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-5 py-3.5 text-slate-500">{o.id}</td>
                      <td className="px-5 py-3.5">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-violet-300 border border-violet-500/20 text-[11px]">
                          {o.persona}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-sans text-xs text-slate-200 leading-relaxed">
                        {o.summary}
                      </td>
                      <td className="px-5 py-3.5 text-right text-amber-300">
                        {o.weight.toFixed(2)}
                      </td>
                      <td className="px-5 py-3.5 text-right text-emerald-300">
                        {(o.confidence * 100).toFixed(0)}%
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {Object.keys(memory.kind_counts).length > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
          <span className="text-slate-500 flex items-center gap-1">
            <Layers className="h-3 w-3" /> by kind:
          </span>
          {Object.entries(memory.kind_counts)
            .sort((a, b) => b[1] - a[1])
            .map(([kind, count]) => (
              <span
                key={kind}
                className="px-2 py-0.5 rounded-full bg-slate-900 border border-slate-800 text-slate-300"
              >
                {kind} <span className="text-cyan-400">{count}</span>
              </span>
            ))}
        </div>
      )}
    </div>
  );
}

export default MemoryExplorer;
