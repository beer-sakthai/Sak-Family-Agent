"use client";

import React, { useState } from "react";
import { Code2, Eye, Terminal, Copy, Check } from "lucide-react";
/**
 * A UI-only shape: this component is a static showcase and reads nothing from
 * the API, so the type lives here rather than in the generated contract, which
 * describes API payloads only. It previously came from `@/lib/types`, which was
 * removed when the data layer moved to `contracts.generated.ts`.
 */
interface StitchScreenPreset {
  id: string;
  title: string;
  category: string;
  prompt: string;
  codeSnippet: string;
  displayMode: "HTML" | "MARKDOWN" | "CODE" | "MERMAID";
  theme: "dark-glassmorphism" | "midnight-emerald" | "cyber-cyan";
}

const STITCH_PRESETS: StitchScreenPreset[] = [
  {
    id: "agent-card",
    title: "SakThai Interactive Agent Drawer",
    category: "Agent UI",
    prompt: "Design a futuristic glassmorphic agent card component for SakThai 1.5B Merged model with real-time status glow, skills badges, and latency sparkline.",
    displayMode: "HTML",
    theme: "dark-glassmorphism",
    codeSnippet: `export function SakThaiAgentCard() {
  return (
    <div className="bg-slate-900/90 backdrop-blur-xl border border-cyan-500/30 p-5 rounded-2xl shadow-2xl shadow-cyan-950/40 hover:border-cyan-400/60 transition-all duration-300">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center text-cyan-400 font-bold">
            ST
          </div>
          <div>
            <h4 className="font-bold text-white text-base">SakThai Plus</h4>
            <p className="text-xs text-slate-400">Primary Orchestrator 1.5B</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/40 text-emerald-400 animate-pulse">
          96.5% Benchmark
        </span>
      </div>
    </div>
  );
}`,
  },
  {
    id: "mermaid-arch",
    title: "Multi-Agent System Architecture",
    category: "Diagram",
    prompt: "Generate a Mermaid flowchart illustrating SakThai Orchestrator routing requests to SakKing (Reasoning), SakSee (Vision), SakSit (Auditor), and SakJules (Async Worker).",
    displayMode: "MERMAID",
    theme: "cyber-cyan",
    codeSnippet: `graph TD
  User["User Request"] --> Orchestrator["SakThai (Primary Orchestrator)"]
  Orchestrator --> Reasoning["SakKing (Reasoning 7B)"]
  Orchestrator --> Vision["SakSee (Vision Multimodal)"]
  Orchestrator --> Auditor["SakSit (Security Auditor)"]
  Orchestrator --> Worker["SakJules (Async Cron Worker)"]`,
  },
  {
    id: "security-badge",
    title: "Security Audit Event Pill",
    category: "Security",
    prompt: "Design a high-visibility security audit log card with severity badges, IP masking, and explicit policy check status.",
    displayMode: "HTML",
    theme: "midnight-emerald",
    codeSnippet: `export function AuditEventCard({ event, severity }: { event: string; severity: string }) {
  return (
    <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-emerald-500/40 transition-all">
      <div className="flex items-center gap-3">
        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
        <span className="text-sm font-medium text-slate-200">{event}</span>
      </div>
      <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/50 text-emerald-400">
        {severity.toUpperCase()}
      </span>
    </div>
  );
}`,
  },
];

export function StitchStudio() {
  const [activePreset, setActivePreset] = useState<StitchScreenPreset>(STITCH_PRESETS[0]);
  const [activeTab, setActiveTab] = useState<"preview" | "code" | "spec">("preview");
  const [copied, setCopied] = useState(false);

  const jsonSpec = JSON.stringify(
    {
      serverUrl: "https://stitch.googleapis.com/mcp",
      protocolVersion: "2024-11-05",
      presetId: activePreset.id,
      theme: activePreset.theme,
      displayMode: activePreset.displayMode,
      screenMetadata: {
        agentType: "GEMINI_3_AGENT",
        status: "COMPLETE",
        displayMode: activePreset.displayMode,
        summary: activePreset.prompt,
      },
    },
    null,
    2
  );

  const handleCopyCode = () => {
    const textToCopy = activeTab === "spec" ? jsonSpec : activePreset.codeSnippet;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-cyan-950/60 via-slate-900/90 to-purple-950/60 border border-cyan-500/30 p-6 shadow-2xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 bg-cyan-950/80 px-2.5 py-0.5 rounded-full border border-cyan-800/50">
                Stitch MCP Studio ⚡
              </span>
            </div>
            <h2 className="text-2xl font-extrabold text-white tracking-tight font-display">
              Google Stitch Design & Component Workbench
            </h2>
            <p className="text-sm text-slate-400 max-w-2xl mt-1">
              Generate, preview, and inspect glassmorphic UI design components and Mermaid architecture diagrams powered by Google Stitch MCP.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-emerald-400 bg-emerald-950/80 px-3 py-1.5 rounded-xl border border-emerald-500/40 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Stitch MCP Connected
            </span>
          </div>
        </div>
      </div>

      {/* Preset Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {STITCH_PRESETS.map((preset) => {
          const isSelected = activePreset.id === preset.id;
          return (
            <button
              key={preset.id}
              type="button"
              aria-pressed={isSelected}
              aria-label={`Select preset ${preset.title}`}
              onClick={() => setActivePreset(preset)}
              className={`text-left p-4 rounded-xl transition-all border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-950 ${
                isSelected
                  ? "bg-cyan-950/40 border-cyan-500/60 shadow-lg shadow-cyan-950/30"
                  : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-cyan-400 font-semibold">{preset.category}</span>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {preset.displayMode}
                </span>
              </div>
              <h4 className="text-sm font-bold text-white mb-1">{preset.title}</h4>
              <p className="text-xs text-slate-400 line-clamp-2">{preset.prompt}</p>
            </button>
          );
        })}
      </div>

      {/* Interactive Workbench Container */}
      <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800/80 rounded-2xl overflow-hidden shadow-2xl">
        {/* Workspace Toolbar */}
        <div className="flex items-center justify-between border-b border-slate-800 px-5 py-3 bg-slate-950/50">
          <div role="tablist" aria-label="Stitch Studio view options" className="flex items-center gap-2">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "preview"}
              onClick={() => setActiveTab("preview")}
              className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
                activeTab === "preview"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              Live Preview
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "code"}
              onClick={() => setActiveTab("code")}
              className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
                activeTab === "code"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              TSX Code
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "spec"}
              onClick={() => setActiveTab("spec")}
              className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
                activeTab === "spec"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              Stitch JSON Spec
            </button>
          </div>

          <button
            type="button"
            aria-live="polite"
            aria-label={copied ? "Copied to clipboard" : activeTab === "spec" ? "Copy Stitch JSON spec" : "Copy TSX code"}
            onClick={handleCopyCode}
            className="flex items-center gap-1 text-xs font-mono text-slate-400 hover:text-cyan-400 transition-colors bg-slate-800/60 px-2.5 py-1 rounded-lg border border-slate-700/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "Copied!" : activeTab === "spec" ? "Copy Spec" : "Copy Code"}
          </button>
        </div>

        {/* Tab Body Content */}
        <div className="p-6">
          {activeTab === "preview" && (
            <div className="min-h-[240px] flex flex-col items-center justify-center p-8 rounded-xl bg-slate-950/80 border border-slate-800/60">
              {activePreset.displayMode === "HTML" && (
                <div className="w-full max-w-md bg-slate-900/90 backdrop-blur-xl border border-cyan-500/30 p-6 rounded-2xl shadow-2xl space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center text-cyan-400 font-bold font-mono">
                        ST
                      </div>
                      <div>
                        <h4 className="font-bold text-white text-base">SakThai Plus 1.5B</h4>
                        <p className="text-xs text-slate-400">Primary Fine-Tuned Agent</p>
                      </div>
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/40 text-emerald-400">
                      96.5% Benchmark
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/40 text-cyan-400">routing</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/40 text-cyan-400">planning</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/40 text-cyan-400">tool-call</span>
                  </div>
                </div>
              )}

              {activePreset.displayMode === "MERMAID" && (
                <div className="w-full max-w-lg p-6 rounded-xl bg-slate-900/90 border border-cyan-500/30 space-y-3 font-mono text-xs text-cyan-300">
                  <div className="text-slate-400 border-b border-slate-800 pb-2 flex items-center justify-between">
                    <span>Mermaid Architecture Spec</span>
                    <span className="text-[10px] text-emerald-400">Rendered</span>
                  </div>
                  <pre className="whitespace-pre-wrap leading-relaxed">{activePreset.codeSnippet}</pre>
                </div>
              )}
            </div>
          )}

          {activeTab === "code" && (
            <pre className="p-4 rounded-xl bg-slate-950 text-slate-300 font-mono text-xs overflow-x-auto border border-slate-800/80 leading-relaxed">
              <code>{activePreset.codeSnippet}</code>
            </pre>
          )}

          {activeTab === "spec" && (
            <pre className="p-4 rounded-xl bg-slate-950 text-cyan-400 font-mono text-xs overflow-x-auto border border-slate-800/80 leading-relaxed">
              <code>{jsonSpec}</code>
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}

export default StitchStudio;
