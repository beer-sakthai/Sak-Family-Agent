"use client";

import { useState } from "react";
import { KnowledgeGraphData, TelegramBridgeData } from "@/lib/types";
import { getKnowledgeGraphData, getTelegramBridgeData } from "@/lib/memoryRag";
import { Database, Send, Search, Network, Radio, CheckCircle, MessageSquare, Mic } from "lucide-react";

export function MemoryRagTelegramPanel() {
  const [graph] = useState<KnowledgeGraphData>(getKnowledgeGraphData());
  const [telegram] = useState<TelegramBridgeData>(getTelegramBridgeData());
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    const hits = graph.nodes.filter((n) =>
      n.label.toLowerCase().includes(searchQuery.toLowerCase())
    );
    setSearchResults(
      `Found ${hits.length} semantic matches in ${graph.dbPath}: ${hits.map((h) => h.label).join(", ") || "None"}`
    );
  };

  return (
    <section className="space-y-6" data-testid="memory-rag-telegram-panel">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-purple-950/40 via-purple-900/20 to-zinc-900 border border-purple-800/40 rounded-xl p-5 backdrop-blur-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
              Trust Stage · 5.0
            </span>
            <span className="text-xs text-zinc-400">Leads: SakTan & SakJules</span>
          </div>
          <h2 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
            <Database className="w-6 h-6 text-purple-400" />
            Memory Vector RAG & Telegram Voice Bridge
          </h2>
          <p className="text-sm text-zinc-400 mt-1 max-w-2xl">
            Persistent SQLite knowledge graph, semantic vector indexing, and bidirectional Telegram agent bot bridge.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-zinc-900/80 border border-zinc-800 px-3.5 py-2 rounded-lg text-center">
            <div className="text-xl font-bold text-purple-400">{graph.totalFacts}</div>
            <div className="text-[11px] text-zinc-400 font-medium uppercase tracking-wider">Indexed Facts</div>
          </div>
          <div className="bg-zinc-900/80 border border-zinc-800 px-3.5 py-2 rounded-lg text-center">
            <div className="text-xl font-bold text-emerald-400">{telegram.activeSessions}</div>
            <div className="text-[11px] text-zinc-400 font-medium uppercase tracking-wider">Active Bot Sessions</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Knowledge Graph Inspector & Vector Search */}
        <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Network className="w-4 h-4 text-purple-400" />
              SQLite Knowledge Graph Entities
            </h3>
            <span className="text-[11px] font-mono text-zinc-400">{graph.dbPath}</span>
          </div>

          {/* Node Cloud */}
          <div className="p-3 bg-zinc-950 rounded-xl border border-zinc-800 flex flex-wrap gap-2">
            {graph.nodes.map((node) => (
              <span
                key={node.id}
                style={{ borderColor: node.color || "#a855f7" }}
                className="px-2.5 py-1 rounded-lg text-xs bg-zinc-900 border text-zinc-200 font-medium flex items-center gap-1.5"
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: node.color || "#a855f7" }}
                />
                {node.label}
              </span>
            ))}
          </div>

          {/* Vector Search Sandbox */}
          <div className="space-y-2 pt-2">
            <label className="text-xs font-semibold text-zinc-300">Semantic Vector Query Sandbox</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Search facts (e.g. Hugging Face, Sentinel, Turbopack)..."
                className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-purple-500"
              />
              <button
                onClick={handleSearch}
                className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <Search className="w-3.5 h-3.5" />
                Query
              </button>
            </div>
            {searchResults && (
              <div className="p-2.5 rounded bg-zinc-950 border border-zinc-800 text-xs text-purple-300 font-mono">
                {searchResults}
              </div>
            )}
          </div>
        </div>

        {/* Right: Telegram Bridge Status & Commands */}
        <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Send className="w-4 h-4 text-cyan-400" />
              Telegram Multi-Agent Bot Bridge
            </h3>
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-semibold flex items-center gap-1">
              <Radio className="w-3 h-3 animate-pulse" />
              {telegram.status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-zinc-950 rounded-lg border border-zinc-800">
              <div className="text-zinc-400 text-[11px]">Bot Username</div>
              <div className="font-mono text-cyan-300 font-semibold mt-0.5">{telegram.botUsername}</div>
            </div>
            <div className="p-3 bg-zinc-950 rounded-lg border border-zinc-800">
              <div className="text-zinc-400 text-[11px]">Voice Transcriber</div>
              <div className="text-emerald-400 font-semibold flex items-center gap-1 mt-0.5">
                <Mic className="w-3.5 h-3.5" />
                Active (Whisper)
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-xs font-semibold text-zinc-300">Registered Bot Commands</div>
            <div className="grid grid-cols-2 gap-2">
              {telegram.registeredCommands.map((cmd) => (
                <div
                  key={cmd}
                  className="px-2.5 py-1.5 bg-zinc-950 rounded border border-zinc-800 font-mono text-[11px] text-zinc-300 flex items-center gap-1.5"
                >
                  <MessageSquare className="w-3 h-3 text-cyan-400" />
                  {cmd}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
