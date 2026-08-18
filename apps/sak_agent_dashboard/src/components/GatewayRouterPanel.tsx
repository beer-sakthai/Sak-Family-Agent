"use client";

import React, { useState } from "react";

interface RouteResult {
  selectedPersona: string;
  roleDeclaration: string;
  intent: string;
  confidence: number;
  matchedKeywords: string[];
  chargeLevel: number;
  reply: string;
}

const PRESET_QUERIES = [
  { label: "🛠️ CI/CD Pipeline Fix", text: "Fix failing docker build in GitHub Actions workflow" },
  { label: "🔍 Research Papers", text: "Find recent arXiv papers on multimodal tool calling benchmarks" },
  { label: "📊 PowerPoint Deck", text: "Generate a PowerPoint pitch deck with slide visual layouts" },
  { label: "✍️ Marketing Copy", text: "Draft a creative newsletter and social media marketing copy" },
  { label: "📅 Daily Operations", text: "Log today's operations schedule and quote service pricing" },
  { label: "🧠 Core Python Code", text: "Refactor core algorithm to optimize memory and type safety" },
];

export default function GatewayRouterPanel() {
  const [prompt, setPrompt] = useState("");
  const [preferredPersona, setPreferredPersona] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RouteResult | null>(null);

  const handleRoute = async (customPrompt?: string) => {
    const textToRoute = customPrompt || prompt;
    if (!textToRoute.trim()) return;

    setLoading(true);
    try {
      const res = await fetch("/api/gateway", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: textToRoute,
          preferred_persona: preferredPersona || undefined,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setResult(data);
      }
    } catch (err) {
      console.error("Gateway routing error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl text-slate-100 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>🌐</span> Multi-Agent Gateway Router & Session Manager
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Dynamic heuristic intent classifier routing queries across all 6 Sak-Family personas.
          </p>
        </div>
        <span className="px-3 py-1 bg-emerald-950 border border-emerald-700 text-emerald-300 text-xs font-semibold rounded-full flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Gateway Active
        </span>
      </div>

      {/* Preset Buttons */}
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
          Query Presets
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {PRESET_QUERIES.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setPrompt(preset.text);
                handleRoute(preset.text);
              }}
              className="text-left text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg p-2.5 transition text-slate-300 hover:text-white"
            >
              <div className="font-medium text-slate-200">{preset.label}</div>
              <div className="text-[10px] text-slate-400 truncate mt-0.5">{preset.text}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Input Form */}
      <div className="space-y-3">
        <div className="flex gap-3">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleRoute()}
            placeholder="Type query or use @sakjules, @saksee, etc..."
            className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <select
            value={preferredPersona}
            onChange={(e) => setPreferredPersona(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">Auto-Route Intent</option>
            <option value="sakthai">SakThai (Reasoning)</option>
            <option value="sakking">SakKing (Architecture)</option>
            <option value="saksee">SakSee (Research)</option>
            <option value="saksit">SakSit (Copywriting)</option>
            <option value="sakjules">SakJules (CI/CD)</option>
            <option value="saktan">SakTan (Operations)</option>
          </select>
          <button
            type="button"
            onClick={() => handleRoute()}
            disabled={loading || !prompt.trim()}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold rounded-lg shadow-md transition flex items-center gap-2"
          >
            {loading ? "Routing..." : "Dispatch Query"}
          </button>
        </div>
      </div>

      {/* Result Display */}
      {result && (
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-400">Routed Persona:</span>
              <span className="px-2.5 py-1 bg-indigo-950 border border-indigo-700 text-indigo-300 text-xs font-bold rounded-md">
                {`@${result.selectedPersona}`}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <span>Intent: <strong className="text-slate-200">{result.intent}</strong></span>
              <span>Confidence: <strong className="text-emerald-400">{(result.confidence * 100).toFixed(0)}%</strong></span>
              <span>Charge: <strong className="text-cyan-400">{result.chargeLevel}%</strong></span>
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Persona Declaration & Response
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 font-mono whitespace-pre-wrap">
              {result.reply}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
