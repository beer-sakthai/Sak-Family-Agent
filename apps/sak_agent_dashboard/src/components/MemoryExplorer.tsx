"use client";

import React, { useState } from "react";
import { Database, Lightbulb, BookOpen, Layers } from "lucide-react";
import { MemoryData } from "@/lib/types";

interface MemoryExplorerProps {
  memory: MemoryData;
}

export function MemoryExplorer({ memory }: MemoryExplorerProps) {
  const [activeTab, setActiveTab] = useState<"facts" | "observations">("facts");

  const facts = memory?.facts || [];
  const observations = memory?.observations || [];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Database className="h-5 w-5 text-emerald-400" />
            SQLite Memory Store Explorer (`memory.db`)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Inspect persistent agent memory facts and synthesis observations loaded from runtime database
          </p>
        </div>

        {/* Tab Selector */}
        <div role="tablist" aria-label="Memory Database Explorer Views" className="flex items-center p-1 rounded-xl bg-slate-950/80 border border-slate-800/80 font-mono text-xs w-fit">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "facts"}
            aria-label={`View memory facts (${facts.length})`}
            onClick={() => setActiveTab("facts")}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-950 ${
              activeTab === "facts"
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-lg shadow-emerald-950/50"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <BookOpen className="h-3.5 w-3.5" />
            Facts ({facts.length})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "observations"}
            aria-label={`View synthesis observations (${observations.length})`}
            onClick={() => setActiveTab("observations")}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-950 ${
              activeTab === "observations"
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-lg shadow-emerald-950/50"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Lightbulb className="h-3.5 w-3.5" />
            Observations ({observations.length})
          </button>
        </div>
      </div>

      {/* Facts View */}
      {activeTab === "facts" && (
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-5 py-3">ID</th>
                  <th className="px-5 py-3">Entity / Key</th>
                  <th className="px-5 py-3">Fact Statement</th>
                  <th className="px-5 py-3">Persona / Source</th>
                  <th className="px-5 py-3 text-right">Created At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {facts.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-8 text-center text-slate-500 italic">
                      No memory facts found in database.
                    </td>
                  </tr>
                ) : (
                  facts.map((f) => (
                    <tr key={f.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-5 py-3.5 text-slate-500">{f.id}</td>
                      <td className="px-5 py-3.5 font-bold text-cyan-300">{f.entity}</td>
                      <td className="px-5 py-3.5 font-sans text-xs text-slate-200 leading-relaxed">
                        {f.fact}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-emerald-400 border border-emerald-500/20 text-[11px]">
                          {f.persona || "System"}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right text-slate-500 text-[11px]">
                        {f.createdAt || "N/A"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Observations View */}
      {activeTab === "observations" && (
        <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-5 py-3">ID</th>
                  <th className="px-5 py-3">Category</th>
                  <th className="px-5 py-3">Observation Summary</th>
                  <th className="px-5 py-3 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {observations.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-5 py-8 text-center text-slate-500 italic">
                      No synthesis observations found in database.
                    </td>
                  </tr>
                ) : (
                  observations.map((o) => (
                    <tr key={o.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-5 py-3.5 text-slate-500">{o.id}</td>
                      <td className="px-5 py-3.5">
                        <span className="px-2 py-0.5 rounded bg-purple-950/50 text-purple-300 border border-purple-800/30 text-[11px]">
                          {o.category}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-sans text-xs text-slate-200 leading-relaxed">
                        {o.observation}
                      </td>
                      <td className="px-5 py-3.5 text-right text-slate-500 text-[11px]">
                        {o.timestamp || "N/A"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default MemoryExplorer;
