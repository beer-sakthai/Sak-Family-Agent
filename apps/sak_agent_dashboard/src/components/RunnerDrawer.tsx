"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  CheckCircle2,
  Copy,
  Maximize2,
  Minimize2,
  Play,
  Shield,
  Square,
  Terminal,
  Trash2,
  X,
  Zap,
} from "lucide-react";

import PersonaAvatar from "./PersonaAvatar";

export interface RunnerDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  initialPersona?: string;
  initialTask?: string;
}

interface LogEntry {
  id: string;
  type: "stdout" | "stderr" | "status" | "error" | "exit";
  text: string;
  timestamp: string;
}

const RUNNER_PERSONAS = [
  {
    id: "sakthai",
    name: "SakThai",
    role: "Lead · HF Master",
    accent: "text-amber-400",
    border: "border-amber-500/30",
    bg: "bg-amber-500/10",
    presets: [
      "Inspect Hugging Face model routers and space sync",
      "Run system health and memory shard diagnostics",
      "Validate core agent contracts",
    ],
  },
  {
    id: "sakking",
    name: "SakKing",
    role: "Runner · Coder",
    accent: "text-blue-400",
    border: "border-blue-500/30",
    bg: "bg-blue-500/10",
    presets: [
      "Run fast test suite verification",
      "Analyze repository dependencies and dead code",
      "Review code simplifier opportunities",
    ],
  },
  {
    id: "saksee",
    name: "SakSee",
    role: "Web / Browser",
    accent: "text-cyan-400",
    border: "border-cyan-500/30",
    bg: "bg-cyan-500/10",
    presets: [
      "Probe dashboard accessibility and contrast",
      "Inspect responsive mobile layout and CSS tokens",
      "Audit browser local storage and url state",
    ],
  },
  {
    id: "sakjules",
    name: "SakJules",
    role: "Automation & CI/CD Master",
    accent: "text-purple-400",
    border: "border-purple-500/30",
    bg: "bg-purple-500/10",
    presets: [
      "Check CI status and verify contracts",
      "Audit Dependabot configuration and lockfile hygiene",
      "Run dry-run quality gates across personas",
    ],
  },
  {
    id: "saksit",
    name: "SakSit",
    role: "Social & GEO Specialist",
    accent: "text-pink-400",
    border: "border-pink-500/30",
    bg: "bg-pink-500/10",
    presets: [
      "Draft bilingual Thai/English release update",
      "Inspect Hugging Face Hub downloads and metadata",
      "Generate milestone social asset bundle",
    ],
  },
  {
    id: "saktan",
    name: "SakTan",
    role: "Daily Ops & Rhythm",
    accent: "text-emerald-400",
    border: "border-emerald-500/30",
    bg: "bg-emerald-500/10",
    presets: [
      "Check daily ops rhythm and heartbeat",
      "Verify memory database integrity and backup",
      "Inspect local Ollama provider status",
    ],
  },
];

export function RunnerDrawer({
  isOpen,
  onClose,
  initialPersona = "sakjules",
  initialTask = "",
}: RunnerDrawerProps) {
  const [selectedPersona, setSelectedPersona] = useState<string>(initialPersona);
  const [taskInput, setTaskInput] = useState<string>(initialTask);
  const [dryRun, setDryRun] = useState<boolean>(true);
  const [fastTrack, setFastTrack] = useState<boolean>(false);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [copied, setCopied] = useState<boolean>(false);
  const [autoScroll, setAutoScroll] = useState<boolean>(true);

  const [prevInitialPersona, setPrevInitialPersona] = useState<string>(initialPersona);
  const [prevInitialTask, setPrevInitialTask] = useState<string>(initialTask);

  if (initialPersona !== prevInitialPersona) {
    setPrevInitialPersona(initialPersona);
    setSelectedPersona(initialPersona);
  }
  if (initialTask !== prevInitialTask) {
    setPrevInitialTask(initialTask);
    setTaskInput(initialTask);
  }

  const abortControllerRef = useRef<AbortController | null>(null);
  const terminalRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll terminal
  useEffect(() => {
    if (autoScroll && terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // Handle escape to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const activePersonaConfig =
    RUNNER_PERSONAS.find((p) => p.id === selectedPersona) || RUNNER_PERSONAS[3];

  const appendLog = useCallback((type: LogEntry["type"], text: string) => {
    setLogs((prev) => [
      ...prev,
      {
        id: `${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        type,
        text,
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);
  }, []);

  const handleAbort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      appendLog("status", "[RUNNER] Process aborted by user.");
      setIsRunning(false);
    }
  }, [appendLog]);

  const handleRun = useCallback(async () => {
    if (!taskInput.trim() || isRunning) return;

    setIsRunning(true);
    appendLog(
      "status",
      `[RUNNER] Initiating ${dryRun ? "DRY-RUN PREFLIGHT" : "LIVE RUN"} for ${activePersonaConfig.name}...`
    );

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch("/api/gateway/runner", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          persona: selectedPersona,
          task: taskInput.trim(),
          dryRun,
          fast: fastTrack,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        appendLog(
          "error",
          `[HTTP ${response.status}] ${errorData.error || "Failed to start runner."}`
        );
        setIsRunning(false);
        return;
      }

      if (!response.body) {
        appendLog("error", "No readable stream returned by runner.");
        setIsRunning(false);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data:")) {
            try {
              const event = JSON.parse(trimmed.slice(5).trim());
              if (event.type === "stdout") {
                appendLog("stdout", event.text);
              } else if (event.type === "stderr") {
                appendLog("stderr", event.text);
              } else if (event.type === "status") {
                appendLog(
                  "status",
                  `[STATUS: ${event.status}] ${event.cmd || ""}`
                );
              } else if (event.type === "error") {
                appendLog("error", event.error);
              } else if (event.type === "exit") {
                appendLog(
                  "exit",
                  `[EXIT] Process finished with exit code ${event.code}`
                );
              }
            } catch {
              // Parse error on malformed event chunk
            }
          }
        }
      }
    } catch (err: unknown) {
      if ((err as Error)?.name === "AbortError") {
        // Handled in handleAbort
      } else {
        const msg = err instanceof Error ? err.message : String(err);
        appendLog("error", `[NETWORK ERROR] ${msg}`);
      }
    } finally {
      setIsRunning(false);
      abortControllerRef.current = null;
    }
  }, [
    taskInput,
    isRunning,
    dryRun,
    fastTrack,
    selectedPersona,
    activePersonaConfig.name,
    appendLog,
  ]);

  const handleCopyLogs = useCallback(() => {
    const raw = logs.map((l) => `[${l.timestamp}] ${l.text}`).join("\n");
    navigator.clipboard.writeText(raw).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [logs]);

  if (!isOpen) return null;

  return (
    <aside
      aria-label="Agent execution runner"
      className={`fixed inset-x-0 bottom-0 z-50 flex flex-col border-t border-line bg-canvas/95 backdrop-blur-md shadow-2xl transition-all duration-300 ease-in-out ${
        isExpanded ? "h-[85vh]" : "h-[480px]"
      }`}
    >
      {/* Top Header Bar */}
      <div className="flex h-12 items-center justify-between border-b border-line px-4 bg-panel/70">
        <div className="flex items-center gap-3">
          <Terminal className="h-4 w-4 text-hue-cyan" />
          <span className="font-mono text-xs font-semibold uppercase tracking-wider text-fg">
            Universal Agent Runner
          </span>
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 font-mono text-[10px] font-medium border ${activePersonaConfig.bg} ${activePersonaConfig.accent} ${activePersonaConfig.border}`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
            {activePersonaConfig.name}
          </span>
          {isRunning && (
            <span className="inline-flex items-center gap-1 text-[11px] font-mono text-amber-400 animate-pulse">
              <span className="h-2 w-2 rounded-full bg-amber-400" />
              Executing...
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? "Collapse height" : "Expand height"}
            className="rounded p-1 text-fg-3 hover:bg-raised hover:text-fg"
          >
            {isExpanded ? (
              <Minimize2 className="h-3.5 w-3.5" />
            ) : (
              <Maximize2 className="h-3.5 w-3.5" />
            )}
          </button>
          <button
            type="button"
            onClick={onClose}
            title="Close Runner (Esc)"
            className="rounded p-1 text-fg-3 hover:bg-raised hover:text-fg"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Main Drawer Body: Controls + Terminal */}
      <div className="grid flex-1 grid-cols-1 lg:grid-cols-12 overflow-hidden">
        {/* Left Column: Persona Selector & Task Formulation (5 cols) */}
        <div className="flex flex-col border-b lg:border-b-0 lg:border-r border-line p-3 overflow-y-auto lg:col-span-5 space-y-3 bg-panel/30">
          {/* Persona Tabs */}
          <div>
            <label className="text-[10px] font-mono uppercase tracking-wider text-fg-3">
              Target Persona
            </label>
            <div className="mt-1.5 grid grid-cols-3 gap-1.5 sm:grid-cols-6">
              {RUNNER_PERSONAS.map((p) => {
                const isSelected = p.id === selectedPersona;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setSelectedPersona(p.id)}
                    className={`flex flex-col items-center justify-center rounded border p-1.5 text-center transition-all ${
                      isSelected
                        ? `${p.bg} ${p.border} ${p.accent} shadow-sm font-semibold`
                        : "border-line bg-panel hover:bg-raised text-fg-2"
                    }`}
                  >
                    <PersonaAvatar name={p.id} size={20} />
                    <span className="mt-1 text-[11px] leading-tight font-mono">
                      {p.name}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Quick Presets for Selected Persona */}
          <div>
            <label className="text-[10px] font-mono uppercase tracking-wider text-fg-3">
              Prompt Presets
            </label>
            <div className="mt-1 flex flex-wrap gap-1">
              {activePersonaConfig.presets.map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setTaskInput(preset)}
                  className="rounded border border-line bg-panel px-2 py-0.5 text-[10px] text-fg-3 hover:border-hue-cyan hover:text-fg font-mono transition-colors"
                >
                  {preset}
                </button>
              ))}
            </div>
          </div>

          {/* Task Prompt Input */}
          <div className="flex-1 flex flex-col">
            <label className="text-[10px] font-mono uppercase tracking-wider text-fg-3">
              Instruction Prompt
            </label>
            <textarea
              value={taskInput}
              onChange={(e) => setTaskInput(e.target.value)}
              onKeyDown={(e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                  e.preventDefault();
                  handleRun();
                }
              }}
              placeholder={`Enter task prompt for ${activePersonaConfig.name}... (Ctrl+Enter to run)`}
              rows={3}
              className="mt-1 w-full flex-1 rounded border border-line bg-sunken p-2 font-mono text-xs text-fg placeholder:text-fg-4 focus:border-hue-cyan focus:outline-none resize-none"
            />
          </div>

          {/* Controls: Dry Run, Fast Track, Submit / Abort */}
          <div className="flex items-center justify-between gap-2 pt-1 border-t border-line">
            <div className="flex items-center gap-3">
              <label
                className="flex items-center gap-1.5 text-[11px] font-mono text-fg-2 cursor-pointer select-none"
                title="Validate without calling paid LLM APIs"
              >
                <input
                  type="checkbox"
                  checked={dryRun}
                  onChange={(e) => setDryRun(e.target.checked)}
                  className="rounded border-line text-hue-cyan focus:ring-0"
                />
                <Shield className="h-3 w-3 text-emerald-400" />
                Dry-run
              </label>

              <label
                className="flex items-center gap-1.5 text-[11px] font-mono text-fg-2 cursor-pointer select-none"
                title="Fast-track mode (bypasses 6-stage cycle)"
              >
                <input
                  type="checkbox"
                  checked={fastTrack}
                  onChange={(e) => setFastTrack(e.target.checked)}
                  className="rounded border-line text-hue-cyan focus:ring-0"
                />
                <Zap className="h-3 w-3 text-amber-400" />
                Fast
              </label>
            </div>

            <div className="flex items-center gap-2">
              {isRunning ? (
                <button
                  type="button"
                  onClick={handleAbort}
                  className="inline-flex items-center gap-1.5 rounded bg-rose-500/20 border border-rose-500/40 px-3 py-1.5 font-mono text-xs font-semibold text-rose-300 hover:bg-rose-500/30 transition-colors"
                >
                  <Square className="h-3.5 w-3.5 fill-current" />
                  Abort
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleRun}
                  disabled={!taskInput.trim()}
                  className="inline-flex items-center gap-1.5 rounded bg-hue-cyan/20 border border-hue-cyan/40 px-3 py-1.5 font-mono text-xs font-semibold text-hue-cyan hover:bg-hue-cyan/30 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <Play className="h-3.5 w-3.5 fill-current" />
                  Execute
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Terminal Streaming Output (7 cols) */}
        <div className="flex flex-col bg-slate-950 p-2 lg:col-span-7 h-full overflow-hidden">
          {/* Terminal Toolbar */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-1 px-1 text-[11px] font-mono text-slate-400">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>stdout / stderr stream</span>
            </div>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1 text-[10px] text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                  className="h-2.5 w-2.5 rounded bg-slate-800"
                />
                Autoscroll
              </label>
              <button
                type="button"
                onClick={handleCopyLogs}
                disabled={logs.length === 0}
                className="rounded p-1 hover:bg-slate-800 text-slate-300 disabled:opacity-30 cursor-pointer"
                title={copied ? "Copied to clipboard!" : "Copy all logs"}
              >
                {copied ? <CheckCircle2 className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
              </button>
              <button
                type="button"
                onClick={() => setLogs([])}
                disabled={logs.length === 0}
                className="rounded p-1 hover:bg-slate-800 text-slate-300 disabled:opacity-30"
                title="Clear logs"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          </div>

          {/* Terminal Logs Content */}
          <div
            ref={terminalRef}
            className="flex-1 overflow-y-auto font-mono text-xs p-2 leading-relaxed select-text space-y-1"
          >
            {logs.length === 0 ? (
              <div className="flex h-full items-center justify-center text-slate-600 italic">
                Ready for task execution. Output will stream here.
              </div>
            ) : (
              logs.map((log) => {
                let color = "text-slate-200";
                if (log.type === "stderr") color = "text-amber-400";
                if (log.type === "error") color = "text-rose-400 font-semibold";
                if (log.type === "status") color = "text-cyan-400 font-semibold";
                if (log.type === "exit")
                  color = "text-emerald-400 font-bold border-t border-slate-800 pt-1";

                return (
                  <div key={log.id} className={`break-words whitespace-pre-wrap ${color}`}>
                    <span className="text-slate-600 text-[10px] mr-2 select-none">
                      {log.timestamp}
                    </span>
                    {log.text}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}

export default RunnerDrawer;
