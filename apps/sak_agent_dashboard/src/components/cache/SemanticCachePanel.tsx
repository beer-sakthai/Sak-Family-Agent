'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  SemanticCacheEntry,
  CacheAnalytics,
  CacheLookupResult,
} from '@/lib/cache/types';
import { SemanticCacheEngine } from '@/lib/cache/semanticCacheEngine';
import {
  Zap,
  DollarSign,
  Cpu,
  Layers,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  Trash2,
  RefreshCw,
  Sparkles,
  Gauge,
} from 'lucide-react';

export const SemanticCachePanel: React.FC = () => {
  const [analytics, setAnalytics] = useState<CacheAnalytics>(
    SemanticCacheEngine.getAnalytics()
  );
  const [entries, setEntries] = useState<SemanticCacheEntry[]>(
    SemanticCacheEngine.getAllEntries()
  );
  const [searchPrompt, setSearchPrompt] = useState<string>(
    'Generate minimal rootless multi-stage Dockerfile for Next.js 15 app'
  );
  const [selectedPersona, setSelectedPersona] = useState<string>('all');
  const [similarityThreshold, setSimilarityThreshold] = useState<number>(0.85);
  const [lookupResult, setLookupResult] = useState<CacheLookupResult | null>(null);
  const [isLookingUp, setIsLookingUp] = useState<boolean>(false);
  const [filterQuery, setFilterQuery] = useState<string>('');

  const fetchCacheData = useCallback(async () => {
    try {
      const res = await fetch('/api/cache');
      if (res.ok) {
        const json = await res.json();
        if (json.data) {
          if (json.data.analytics) setAnalytics(json.data.analytics);
          if (json.data.entries) setEntries(json.data.entries);
        }
      }
    } catch {
      // In-memory fallback
    }
  }, []);

  useEffect(() => {
    let isSubscribed = true;
    const init = async () => {
      try {
        const res = await fetch('/api/cache');
        if (res.ok) {
          const json = await res.json();
          if (isSubscribed && json.data) {
            if (json.data.analytics) setAnalytics(json.data.analytics);
            if (json.data.entries) setEntries(json.data.entries);
          }
        }
      } catch {
        // In-memory fallback
      }
    };
    void init();
    return () => {
      isSubscribed = false;
    };
  }, []);

  const handleTestLookup = async () => {
    setIsLookingUp(true);
    try {
      const res = await fetch('/api/cache', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'lookup',
          prompt: searchPrompt,
          personaSlug: selectedPersona,
          minSimilarity: similarityThreshold,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.result) {
          setLookupResult(data.result);
          void fetchCacheData();
        }
      } else {
        const localRes = SemanticCacheEngine.lookup({
          prompt: searchPrompt,
          personaSlug: selectedPersona,
          minSimilarity: similarityThreshold,
        });
        setLookupResult(localRes);
        setAnalytics(SemanticCacheEngine.getAnalytics());
      }
    } finally {
      setIsLookingUp(false);
    }
  };

  const handleInvalidate = async (id: string) => {
    try {
      await fetch('/api/cache', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'invalidate', id }),
      });
      setEntries((prev) => prev.filter((e) => e.id !== id));
      setAnalytics(SemanticCacheEngine.getAnalytics());
    } catch {
      SemanticCacheEngine.invalidate(id);
      setEntries(SemanticCacheEngine.getAllEntries());
    }
  };

  const filteredEntries = entries.filter(
    (e) =>
      e.prompt.toLowerCase().includes(filterQuery.toLowerCase()) ||
      e.personaSlug.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Banner Stats Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Cache Hit Ratio</span>
            <Gauge className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">
            {analytics.hitRatePercent}%
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            {analytics.totalHits} hits / {analytics.totalLookups} lookups
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total USD Saved</span>
            <DollarSign className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-300 mt-2">
            ${analytics.totalCostSavedUsd.toFixed(2)}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-medium">
            Zero-Token Re-computation
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Tokens Saved</span>
            <Sparkles className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">
            {(analytics.totalTokensSaved / 1000).toFixed(1)}k
          </div>
          <div className="text-[10px] text-cyan-400 mt-1 font-medium">
            {analytics.cacheSize} Active Embeddings
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Average Cache Latency</span>
            <Zap className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-300 mt-2">
            {analytics.avgLookupLatencyMs}ms
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            vs. ~1,450ms LLM roundtrip
          </div>
        </div>
      </div>

      {/* Interactive Semantic Cache Query Tester */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Search className="w-4 h-4 text-cyan-400" />
            Interactive Semantic Cache Query Tester
          </h3>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/40">
            64-D L2 Cosine
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-3">
            <div>
              <label className="text-[11px] text-slate-400 font-medium block mb-1">
                Query Prompt / Intent:
              </label>
              <textarea
                rows={3}
                value={searchPrompt}
                onChange={(e) => setSearchPrompt(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 font-mono text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex flex-wrap gap-2 text-[10px]">
              <span className="text-slate-500 self-center">Templates:</span>
              <button
                onClick={() =>
                  setSearchPrompt(
                    'Generate minimal rootless multi-stage Dockerfile for Next.js 15 app'
                  )
                }
                className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700"
              >
                Dockerfile
              </button>
              <button
                onClick={() =>
                  setSearchPrompt(
                    'Verify AST safety for shell command git status and check path traversal'
                  )
                }
                className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700"
              >
                AST Safety
              </button>
              <button
                onClick={() =>
                  setSearchPrompt('Decompose full-stack multi-agent orchestration roadmap')
                }
                className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700"
              >
                Multi-Agent
              </button>
            </div>
          </div>

          <div className="space-y-3 bg-slate-950/70 p-3.5 rounded-lg border border-slate-800/80 flex flex-col justify-between">
            <div className="space-y-3">
              <div>
                <label className="text-[11px] text-slate-400 font-medium block mb-1">
                  Persona Scope:
                </label>
                <select
                  value={selectedPersona}
                  onChange={(e) => setSelectedPersona(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded p-1.5 text-xs text-slate-200"
                >
                  <option value="all">Fleet-Wide (All Personas)</option>
                  <option value="sakjules">SakJules (Automation)</option>
                  <option value="saksee">SakSee (Security)</option>
                  <option value="sakking">SakKing (Orchestration)</option>
                  <option value="saktan">SakTan (Analytics)</option>
                  <option value="sakthai">SakThai (Architecture)</option>
                  <option value="saknoi">SakNoi (Creative)</option>
                </select>
              </div>

              <div>
                <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium mb-1">
                  <span>Cosine Similarity Threshold:</span>
                  <span className="font-mono text-cyan-400">
                    {(similarityThreshold * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.70"
                  max="0.99"
                  step="0.01"
                  value={similarityThreshold}
                  onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                  className="w-full accent-cyan-500"
                />
              </div>
            </div>

            <button
              onClick={handleTestLookup}
              disabled={isLookingUp}
              className={`w-full py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-md transition-all ${
                isLookingUp
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-cyan-600 hover:bg-cyan-500 text-white hover:shadow-cyan-500/20'
              }`}
            >
              {isLookingUp ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  Calculating Vector Distance...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 text-cyan-200" />
                  Test Semantic Cache Lookup
                </>
              )}
            </button>
          </div>
        </div>

        {/* Lookup Result Display */}
        {lookupResult && (
          <div className="mt-4 p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {lookupResult.hit ? (
                  <span className="flex items-center gap-1 text-emerald-400 font-bold">
                    <CheckCircle2 className="w-4 h-4" />
                    CACHE HIT
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-rose-400 font-bold">
                    <XCircle className="w-4 h-4" />
                    CACHE MISS
                  </span>
                )}
                <span className="text-[10px] font-mono text-slate-400">
                  Similarity Score: {(lookupResult.similarity * 100).toFixed(1)}%
                </span>
              </div>

              <div className="flex items-center gap-3 font-mono text-[10px] text-slate-400">
                <span>Lookup: {lookupResult.lookupLatencyMs}ms</span>
                {lookupResult.hit && (
                  <span className="text-emerald-400">
                    Saved: ~{lookupResult.latencySavedMs}ms
                  </span>
                )}
              </div>
            </div>

            {lookupResult.entry && (
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">
                    Matched Cached Persona: <span className="text-cyan-400 font-semibold">{lookupResult.entry.personaSlug}</span>
                  </span>
                  <span className="text-amber-400 font-mono">
                    +${(lookupResult.entry.costSavedUsd * lookupResult.entry.hitCount).toFixed(4)} USD Saved
                  </span>
                </div>
                <div className="p-2.5 bg-slate-900 rounded border border-slate-800/80 font-mono text-[11px] text-slate-300 max-h-36 overflow-y-auto whitespace-pre-wrap">
                  {lookupResult.entry.response}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Cache Entries Directory & Invalidation Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-slate-100">
              Active Semantic Cache Entries ({entries.length})
            </h3>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Filter prompt patterns..."
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none"
            />
            <button
              onClick={() => void fetchCacheData()}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700"
              title="Refresh Cache"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
          {filteredEntries.map((entry) => (
            <div
              key={entry.id}
              className="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex items-center justify-between gap-3 text-xs"
            >
              <div className="space-y-1 min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/40">
                    {entry.personaSlug}
                  </span>
                  <span className="font-semibold text-slate-200 truncate">{entry.prompt}</span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono flex items-center gap-3">
                  <span>Hits: <span className="text-cyan-400">{entry.hitCount}</span></span>
                  <span>Tokens: <span className="text-amber-400">{entry.tokensSaved}</span></span>
                  <span>Model: {entry.model}</span>
                </div>
              </div>

              <div className="flex items-center gap-3 flex-shrink-0">
                <span className="text-emerald-400 font-mono text-[11px]">
                  +${(entry.costSavedUsd * entry.hitCount).toFixed(4)}
                </span>
                <button
                  onClick={() => handleInvalidate(entry.id)}
                  className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 rounded transition-colors"
                  title="Invalidate Cache Entry"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
