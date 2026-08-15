"use client";

import React, { useState } from "react";
import {
  Cpu,
  Zap,
  Shield,
  Activity,
  Layers,
  Sparkles,
  Server,
  DollarSign,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { PROVIDERS } from "@/lib/providers";
import { ProviderSpec } from "@/lib/types";

const providerIcons: Record<string, React.ReactNode> = {
  claude: <Sparkles className="h-5 w-5 text-amber-400" />,
  codex: <Zap className="h-5 w-5 text-emerald-400" />,
  opencode: <Cpu className="h-5 w-5 text-cyan-400" />,
  ollama: <Server className="h-5 w-5 text-blue-400" />,
  huggingface: <Layers className="h-5 w-5 text-yellow-400" />,
  gemini_agy: <Activity className="h-5 w-5 text-purple-400" />,
};

export function ProviderMatrixPanel() {
  const [selectedProvider, setSelectedProvider] = useState<ProviderSpec>(PROVIDERS[0]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Cpu className="h-5 w-5 text-cyan-400" />
            Multi-Provider AI Matrix
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/60 font-semibold">
              6 Ecosystems Active
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
            Multi-model inference matrix powering the 6 Sak-Family personas. Automatic fallback routing across Claude, Codex, OpenCode, Ollama Local, Hugging Face, and Gemini / Antigravity AGY.
          </p>
        </div>
      </div>

      {/* 6-Provider Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {PROVIDERS.map((prov) => {
          const isSelected = selectedProvider.id === prov.id;
          const icon = providerIcons[prov.id] || <Cpu className="h-5 w-5 text-cyan-400" />;

          return (
            <div
              key={prov.id}
              onClick={() => setSelectedProvider(prov)}
              className={`p-5 rounded-2xl cursor-pointer transition-all duration-300 flex flex-col justify-between space-y-4 border ${
                isSelected
                  ? "bg-slate-800/90 border-cyan-500/60 shadow-lg shadow-cyan-950/50"
                  : "bg-slate-900/70 border-slate-800/80 hover:border-slate-700 hover:bg-slate-850/80"
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2.5 rounded-xl bg-slate-800/90 border border-slate-700/60 shadow-md">
                    {icon}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white tracking-tight flex items-center gap-1.5">
                      {prov.name}
                      {prov.isLocal && (
                        <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60">
                          LOCAL $0
                        </span>
                      )}
                    </h4>
                    <p className="text-[11px] text-slate-400">{prov.vendor}</p>
                  </div>
                </div>

                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  HEALTHY
                </span>
              </div>

              {/* Description */}
              <p className="text-xs text-slate-300 leading-relaxed line-clamp-2">
                {prov.description}
              </p>

              {/* Stats & Personas */}
              <div className="pt-2 border-t border-slate-800/80 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3 text-cyan-400" />
                    Avg Latency: <strong className="text-slate-200">{prov.latencyMs}ms</strong>
                  </span>
                  <span>{prov.supportedModels.length} Models</span>
                </div>

                {/* Assigned Personas */}
                <div className="flex flex-wrap items-center gap-1 pt-1">
                  <span className="text-[10px] text-slate-500 mr-1">Personas:</span>
                  {prov.assignedPersonas.map((name) => (
                    <span
                      key={name}
                      className="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-800/80 text-cyan-300 border border-slate-700/60"
                    >
                      {name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Provider Model Drilldown Panel */}
      <div className="glass-panel p-6 rounded-2xl bg-slate-900/90 border border-slate-800/80 backdrop-blur-xl shadow-xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
              {providerIcons[selectedProvider.id]}
            </div>
            <div>
              <h4 className="text-base font-bold text-white flex items-center gap-2">
                {selectedProvider.name} — Supported Models & Capabilities
              </h4>
              <p className="text-xs text-slate-400">
                Default production endpoint: <code className="text-cyan-300 font-mono">{selectedProvider.defaultModel}</code>
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {selectedProvider.supportedModels.map((m) => (
            <div
              key={m.id}
              className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700/80 transition-all space-y-3"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h5 className="text-xs font-bold text-slate-100 font-mono">{m.name}</h5>
                  <p className="text-[10px] text-slate-500 font-mono">{m.id}</p>
                </div>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  {m.contextWindow.toLocaleString()} ctx
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-1.5">
                {m.capabilities.map((cap) => (
                  <span
                    key={cap}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                  >
                    <CheckCircle2 className="h-2.5 w-2.5" />
                    {cap}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-900">
                <span className="flex items-center gap-1">
                  <DollarSign className="h-3 w-3 text-emerald-400" />
                  Input: ${m.inputCostPer1M.toFixed(2)}/1M
                </span>
                <span>Output: ${m.outputCostPer1M.toFixed(2)}/1M</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
