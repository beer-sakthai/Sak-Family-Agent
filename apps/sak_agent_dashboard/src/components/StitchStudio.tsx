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
    <div className="bg-panel/90 backdrop-blur-xl border border-hue-cyan-line/30 p-5 rounded-2xl shadow-2xl shadow-hue-cyan-tint/40 hover:border-hue-cyan/60 transition-all duration-300">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-hue-cyan-tint/80 border border-hue-cyan-line/40 flex items-center justify-center text-hue-cyan font-bold">
            ST
          </div>
          <div>
            <h4 className="font-bold text-fg text-base">SakThai Plus</h4>
            <p className="text-xs text-fg-3">Primary Orchestrator 1.5B</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-hue-emerald-tint/60 border border-hue-emerald-line/40 text-hue-emerald animate-pulse">
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
    <div className="flex items-center justify-between p-3.5 rounded-xl bg-panel/60 border border-line/80 hover:border-hue-emerald-line/40 transition-all">
      <div className="flex items-center gap-3">
        <span className="w-2.5 h-2.5 rounded-full bg-hue-emerald shadow-sm shadow-hue-emerald/50" />
        <span className="text-sm font-medium text-fg">{event}</span>
      </div>
      <span className="text-xs font-mono px-2 py-0.5 rounded bg-hue-emerald-tint/60 border border-hue-emerald-line/50 text-hue-emerald">
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

  const tabs = ["preview", "code", "spec"] as const;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      e.preventDefault();
      const currentIndex = tabs.indexOf(activeTab);
      const nextIndex =
        e.key === "ArrowRight"
          ? (currentIndex + 1) % tabs.length
          : (currentIndex - 1 + tabs.length) % tabs.length;
      const nextTab = tabs[nextIndex];
      setActiveTab(nextTab);
      document.getElementById(`stitch-tab-${nextTab}`)?.focus();
    } else if (e.key === "Home") {
      e.preventDefault();
      setActiveTab("preview");
      document.getElementById("stitch-tab-preview")?.focus();
    } else if (e.key === "End") {
      e.preventDefault();
      setActiveTab("spec");
      document.getElementById("stitch-tab-spec")?.focus();
    }
  };

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
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-hue-cyan-tint/60 via-panel/90 to-hue-purple-tint/60 border border-hue-cyan-line/30 p-6 shadow-2xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-hue-cyan bg-hue-cyan-tint/80 px-2.5 py-0.5 rounded-full border border-hue-cyan-line/50">
                Stitch MCP Studio ⚡
              </span>
            </div>
            <h2 className="text-2xl font-extrabold text-fg tracking-tight font-display">
              Google Stitch Design & Component Workbench
            </h2>
            <p className="text-sm text-fg-3 max-w-2xl mt-1">
              Generate, preview, and inspect glassmorphic UI design components and Mermaid architecture diagrams powered by Google Stitch MCP.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-hue-emerald bg-hue-emerald-tint/80 px-3 py-1.5 rounded-xl border border-hue-emerald-line/40 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-hue-emerald animate-pulse" />
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
              className={`text-left p-4 rounded-xl transition-all border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-1 focus-visible:ring-offset-canvas ${
                isSelected
                  ? "bg-hue-cyan-tint/40 border-hue-cyan-line/60 shadow-lg shadow-hue-cyan-tint/30"
                  : "bg-panel/60 border-line hover:border-line-strong"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-hue-cyan font-semibold">{preset.category}</span>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-raised text-fg-2">
                  {preset.displayMode}
                </span>
              </div>
              <h4 className="text-sm font-bold text-fg mb-1">{preset.title}</h4>
              <p className="text-xs text-fg-3 line-clamp-2">{preset.prompt}</p>
            </button>
          );
        })}
      </div>

      {/* Interactive Workbench Container */}
      <div className="bg-panel/80 backdrop-blur-xl border border-line/80 rounded-2xl overflow-hidden shadow-2xl">
        {/* Workspace Toolbar */}
        <div className="flex items-center justify-between border-b border-line px-5 py-3 bg-sunken/50">
          <div
            role="tablist"
            aria-label="Stitch Studio view options"
            onKeyDown={handleKeyDown}
            className="flex items-center gap-2"
          >
            <button
              id="stitch-tab-preview"
              type="button"
              role="tab"
              tabIndex={activeTab === "preview" ? 0 : -1}
              aria-selected={activeTab === "preview"}
              aria-controls="stitch-panel-preview"
              onClick={() => setActiveTab("preview")}
              className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                activeTab === "preview"
                  ? "bg-hue-cyan text-accent-contrast font-bold shadow-md shadow-hue-cyan/20"
                  : "text-fg-3 hover:text-fg"
              }`}
            >
              <Eye className="w-3.5 h-3.5" aria-hidden />
              Live Preview
            </button>
            <button
              id="stitch-tab-code"
              type="button"
              role="tab"
              tabIndex={activeTab === "code" ? 0 : -1}
              aria-selected={activeTab === "code"}
              aria-controls="stitch-panel-code"
              onClick={() => setActiveTab("code")}
              className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                activeTab === "code"
                  ? "bg-hue-cyan text-accent-contrast font-bold shadow-md shadow-hue-cyan/20"
                  : "text-fg-3 hover:text-fg"
              }`}
            >
              <Code2 className="w-3.5 h-3.5" aria-hidden />
              TSX Code
            </button>
            <button
              id="stitch-tab-spec"
              type="button"
              role="tab"
              tabIndex={activeTab === "spec" ? 0 : -1}
              aria-selected={activeTab === "spec"}
              aria-controls="stitch-panel-spec"
              onClick={() => setActiveTab("spec")}
              className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                activeTab === "spec"
                  ? "bg-hue-cyan text-accent-contrast font-bold shadow-md shadow-hue-cyan/20"
                  : "text-fg-3 hover:text-fg"
              }`}
            >
              <Terminal className="w-3.5 h-3.5" aria-hidden />
              Stitch JSON Spec
            </button>
          </div>

          <button
            type="button"
            aria-live="polite"
            aria-label={copied ? "Copied to clipboard" : activeTab === "spec" ? "Copy Stitch JSON spec" : "Copy TSX code"}
            onClick={handleCopyCode}
            className="flex items-center gap-1 text-xs font-mono text-fg-3 hover:text-hue-cyan transition-colors bg-raised/60 px-2.5 py-1 rounded-lg border border-line-strong/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-hue-emerald" aria-hidden /> : <Copy className="w-3.5 h-3.5" aria-hidden />}
            {copied ? "Copied!" : activeTab === "spec" ? "Copy Spec" : "Copy Code"}
          </button>
        </div>

        {/* Tab Body Content */}
        <div
          id={`stitch-panel-${activeTab}`}
          role="tabpanel"
          aria-labelledby={`stitch-tab-${activeTab}`}
          tabIndex={0}
          className="p-6 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded-xl"
        >
          {activeTab === "preview" && (
            <div className="min-h-[240px] flex flex-col items-center justify-center p-8 rounded-xl bg-sunken/80 border border-line/60">
              {activePreset.displayMode === "HTML" && (
                <div className="w-full max-w-md bg-panel/90 backdrop-blur-xl border border-hue-cyan-line/30 p-6 rounded-2xl shadow-2xl space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-hue-cyan-tint/80 border border-hue-cyan-line/40 flex items-center justify-center text-hue-cyan font-bold font-mono">
                        ST
                      </div>
                      <div>
                        <h4 className="font-bold text-fg text-base">SakThai Plus 1.5B</h4>
                        <p className="text-xs text-fg-3">Primary Fine-Tuned Agent</p>
                      </div>
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-hue-emerald-tint/60 border border-hue-emerald-line/40 text-hue-emerald">
                      96.5% Benchmark
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-hue-cyan-tint/60 border border-hue-cyan-line/40 text-hue-cyan">routing</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-hue-cyan-tint/60 border border-hue-cyan-line/40 text-hue-cyan">planning</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-hue-cyan-tint/60 border border-hue-cyan-line/40 text-hue-cyan">tool-call</span>
                  </div>
                </div>
              )}

              {activePreset.displayMode === "MERMAID" && (
                <div className="w-full max-w-lg p-6 rounded-xl bg-panel/90 border border-hue-cyan-line/30 space-y-3 font-mono text-xs text-hue-cyan">
                  <div className="text-fg-3 border-b border-line pb-2 flex items-center justify-between">
                    <span>Mermaid Architecture Spec</span>
                    <span className="text-[10px] text-hue-emerald">Rendered</span>
                  </div>
                  <pre className="whitespace-pre-wrap leading-relaxed">{activePreset.codeSnippet}</pre>
                </div>
              )}
            </div>
          )}

          {activeTab === "code" && (
            <pre className="p-4 rounded-xl bg-sunken text-fg-2 font-mono text-xs overflow-x-auto border border-line/80 leading-relaxed">
              <code>{activePreset.codeSnippet}</code>
            </pre>
          )}

          {activeTab === "spec" && (
            <pre className="p-4 rounded-xl bg-sunken text-hue-cyan font-mono text-xs overflow-x-auto border border-line/80 leading-relaxed">
              <code>{jsonSpec}</code>
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}

export default StitchStudio;
