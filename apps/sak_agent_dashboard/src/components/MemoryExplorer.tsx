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
          <h3 className="text-xl font-bold font-display text-fg tracking-tight flex items-center gap-2">
            <Database className="h-5 w-5 text-hue-emerald" />
            Memory Store Explorer
          </h3>
          <p className="text-xs text-fg-3 mt-0.5">
            Facts and observations merged across every persona&apos;s{" "}
            <code className="text-fg-2">memory.db</code> shard
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1 rounded-full bg-panel border border-line text-hue-cyan">
            {memory.total_facts.toLocaleString()} facts
            {memory.facts_this_week > 0 && (
              <span className="text-hue-emerald"> (+{memory.facts_this_week} this week)</span>
            )}
          </span>
          <span className="px-3 py-1 rounded-full bg-panel border border-line text-hue-violet">
            {memory.total_observations.toLocaleString()} observations
          </span>
        </div>
      </div>

      <div role="tablist" aria-label="Memory Explorer tabs" className="flex items-center gap-2">
        <button
          id="tab-facts"
          role="tab"
          aria-selected={activeTab === "facts"}
          aria-controls="panel-facts"
          onClick={() => setActiveTab("facts")}
          className={`px-4 py-2 rounded-xl text-xs font-mono border transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-canvas ${
            activeTab === "facts"
              ? "bg-hue-cyan-tint/50 text-hue-cyan border-hue-cyan-line/50"
              : "bg-panel/60 text-fg-3 border-line hover:border-line-strong"
          }`}
        >
          <BookOpen className="h-3.5 w-3.5 inline mr-1.5" aria-hidden />
          Facts ({facts.length})
        </button>
        <button
          id="tab-observations"
          role="tab"
          aria-selected={activeTab === "observations"}
          aria-controls="panel-observations"
          onClick={() => setActiveTab("observations")}
          className={`px-4 py-2 rounded-xl text-xs font-mono border transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-canvas ${
            activeTab === "observations"
              ? "bg-hue-violet-tint/50 text-hue-violet border-hue-violet-line/50"
              : "bg-panel/60 text-fg-3 border-line hover:border-line-strong"
          }`}
        >
          <Lightbulb className="h-3.5 w-3.5 inline mr-1.5" aria-hidden />
          Observations ({observations.length})
        </button>
      </div>

      {activeTab === "facts" && (
        <div
          role="tabpanel"
          id="panel-facts"
          aria-labelledby="tab-facts"
          className="glass-panel rounded-2xl bg-panel/80 border border-line/80 backdrop-blur-xl overflow-hidden shadow-xl"
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-sunken/80 text-fg-3 border-b border-line/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-5 py-3">ID</th>
                  <th className="px-5 py-3">Kind / Key</th>
                  <th className="px-5 py-3">Value</th>
                  <th className="px-5 py-3">Shard</th>
                  <th className="px-5 py-3 text-right">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/60 text-fg-2">
                {facts.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-8 text-center text-fg-4 italic">
                      No memory facts found.
                    </td>
                  </tr>
                ) : (
                  facts.map((f) => (
                    <tr key={`${f.persona}-${f.id}`} className="hover:bg-raised/40 transition-colors">
                      <td className="px-5 py-3.5 text-fg-4">{f.id}</td>
                      <td className="px-5 py-3.5 font-bold text-hue-cyan">
                        {f.kind}
                        {f.key && <span className="text-fg-4 font-normal"> / {f.key}</span>}
                      </td>
                      <td className="px-5 py-3.5 font-sans text-xs text-fg leading-relaxed">
                        {f.value}
                        {f.tags.length > 0 && (
                          <span className="ml-2 text-[10px] font-mono text-fg-4">
                            {f.tags.map((t) => `#${t}`).join(" ")}
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="px-2 py-0.5 rounded bg-raised text-hue-emerald border border-hue-emerald-line/20 text-[11px]">
                          {f.persona}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right text-fg-4 text-[11px]">
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
        <div
          role="tabpanel"
          id="panel-observations"
          aria-labelledby="tab-observations"
          className="glass-panel rounded-2xl bg-panel/80 border border-line/80 backdrop-blur-xl overflow-hidden shadow-xl"
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-sunken/80 text-fg-3 border-b border-line/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-5 py-3">ID</th>
                  <th className="px-5 py-3">Shard</th>
                  <th className="px-5 py-3">Observation</th>
                  <th className="px-5 py-3 text-right">Weight</th>
                  <th className="px-5 py-3 text-right">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/60 text-fg-2">
                {observations.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-8 text-center text-fg-4 italic">
                      No observations recorded.
                    </td>
                  </tr>
                ) : (
                  observations.map((o) => (
                    <tr key={`${o.persona}-${o.id}`} className="hover:bg-raised/40 transition-colors">
                      <td className="px-5 py-3.5 text-fg-4">{o.id}</td>
                      <td className="px-5 py-3.5">
                        <span className="px-2 py-0.5 rounded bg-raised text-hue-violet border border-hue-violet-line/20 text-[11px]">
                          {o.persona}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-sans text-xs text-fg leading-relaxed">
                        {o.summary}
                      </td>
                      <td className="px-5 py-3.5 text-right text-hue-amber">
                        {o.weight.toFixed(2)}
                      </td>
                      <td className="px-5 py-3.5 text-right text-hue-emerald">
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
          <span className="text-fg-4 flex items-center gap-1">
            <Layers className="h-3 w-3" /> by kind:
          </span>
          {Object.entries(memory.kind_counts)
            .sort((a, b) => b[1] - a[1])
            .map(([kind, count]) => (
              <span
                key={kind}
                className="px-2 py-0.5 rounded-full bg-panel border border-line text-fg-2"
              >
                {kind} <span className="text-hue-cyan">{count}</span>
              </span>
            ))}
        </div>
      )}
    </div>
  );
}

export default MemoryExplorer;
