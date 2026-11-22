"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Play,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Terminal,
  Layers,
  ArrowRight,
  Loader2,
  Copy,
  Check,
  Workflow,
  Sparkles,
} from "lucide-react";

interface PipelineStepMeta {
  index: number;
  name: string;
  persona: string;
  output_key: string;
  parallel_group?: string | null;
}

interface PipelineDefinitionMeta {
  name: string;
  description: string;
  steps_count: number;
  steps: PipelineStepMeta[];
}

interface StepExecutionState {
  index: number;
  name: string;
  persona: string;
  status: "idle" | "running" | "completed" | "failed";
  output: string;
  tokens: string[];
  duration_ms?: number;
  error?: string;
}

const DEFAULT_PIPELINES: PipelineDefinitionMeta[] = [
  {
    name: "code-review",
    description: "Tri-agent code inspection, CI/CD validation, and test synthesis",
    steps_count: 3,
    steps: [
      { index: 0, name: "code-analysis", persona: "sakthai", output_key: "lead_analysis" },
      { index: 1, name: "ci-validation", persona: "sakjules", output_key: "ci_report" },
      { index: 2, name: "test-synthesis", persona: "saksee", output_key: "test_suite" },
    ],
  },
  {
    name: "research-brief",
    description: "Web deep-dive, architectural synthesis, and executive briefing",
    steps_count: 3,
    steps: [
      { index: 0, name: "topic-framing", persona: "sakthai", output_key: "framing" },
      { index: 1, name: "web-recon", persona: "saksee", output_key: "recon_data" },
      { index: 2, name: "briefing-synthesis", persona: "saksit", output_key: "briefing" },
    ],
  },
  {
    name: "incident-response",
    description: "Triage diagnostics, security policy audit, and runner remediation",
    steps_count: 3,
    steps: [
      { index: 0, name: "triage-diagnostics", persona: "sakthai", output_key: "diagnosis" },
      { index: 1, name: "guardrail-audit", persona: "sakjules", output_key: "audit_findings" },
      { index: 2, name: "remediation-runner", persona: "sakking", output_key: "runner_action" },
    ],
  },
];

const PERSONA_COLORS: Record<string, { bg: string; text: string; border: string; glow: string }> = {
  sakthai: {
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/30",
    glow: "shadow-amber-500/20",
  },
  sakking: {
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/30",
    glow: "shadow-blue-500/20",
  },
  saksee: {
    bg: "bg-cyan-500/10",
    text: "text-cyan-400",
    border: "border-cyan-500/30",
    glow: "shadow-cyan-500/20",
  },
  sakjules: {
    bg: "bg-violet-500/10",
    text: "text-violet-400",
    border: "border-violet-500/30",
    glow: "shadow-violet-500/20",
  },
  saksit: {
    bg: "bg-pink-500/10",
    text: "text-pink-400",
    border: "border-pink-500/30",
    glow: "shadow-pink-500/20",
  },
  saktan: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
    glow: "shadow-emerald-500/20",
  },
};

export function TeamPipelineVisualizer() {
  const [selectedPipelineName, setSelectedPipelineName] = useState<string>("code-review");
  const [taskPrompt, setTaskPrompt] = useState<string>(
    "Audit Gateway SSE streaming and implement live team pipeline DAG visualizer"
  );
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [stepStates, setStepStates] = useState<Record<number, StepExecutionState>>({});
  const [activeStepIndex, setActiveStepIndex] = useState<number | null>(null);
  const [finalOutput, setFinalOutput] = useState<string>("");
  const [totalDurationMs, setTotalDurationMs] = useState<number | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [copied, setCopied] = useState<boolean>(false);

  const terminalRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const currentPipeline =
    DEFAULT_PIPELINES.find((p) => p.name === selectedPipelineName) || DEFAULT_PIPELINES[0];

  // Initialize step states when pipeline selection changes
  useEffect(() => {
    const initialStates: Record<number, StepExecutionState> = {};
    currentPipeline.steps.forEach((step, idx) => {
      initialStates[idx] = {
        index: idx,
        name: step.name,
        persona: step.persona,
        status: "idle",
        output: "",
        tokens: [],
      };
    });
    setStepStates(initialStates);
    setActiveStepIndex(null);
    setFinalOutput("");
    setTotalDurationMs(null);
    setRunId(null);
    setLogs([]);
  }, [selectedPipelineName, currentPipeline]);

  // Auto-scroll terminal when new logs or tokens arrive
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs, stepStates]);

  const handleStartPipeline = async () => {
    if (!taskPrompt.trim() || isExecuting) return;

    setIsExecuting(true);
    setFinalOutput("");
    setTotalDurationMs(null);
    setLogs([`[System] Initializing team pipeline '${selectedPipelineName}'...`]);

    const initialStates: Record<number, StepExecutionState> = {};
    currentPipeline.steps.forEach((step, idx) => {
      initialStates[idx] = {
        index: idx,
        name: step.name,
        persona: step.persona,
        status: "idle",
        output: "",
        tokens: [],
      };
    });
    setStepStates(initialStates);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch("/api/gateway/team/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pipeline: selectedPipelineName,
          task: taskPrompt.trim(),
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`Pipeline stream request failed with status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          const trimmed = block.trim();
          if (!trimmed) continue;

          let eventName = "message";
          let eventData = "";

          for (const line of trimmed.split("\n")) {
            if (line.startsWith("event: ")) {
              eventName = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              eventData = line.slice(6).trim();
            }
          }

          if (eventData === "[DONE]" || eventName === "done") {
            setLogs((prev) => [...prev, "[System] Team pipeline execution completed."]);
            continue;
          }

          try {
            const parsed = JSON.parse(eventData);

            if (eventName === "pipeline_start") {
              setRunId(parsed.run_id);
              setLogs((prev) => [
                ...prev,
                `[Pipeline Started] Run ID: ${parsed.run_id} | Total Steps: ${parsed.total_steps}`,
              ]);
            } else if (eventName === "step_start") {
              const stepIdx = parsed.step_index;
              setActiveStepIndex(stepIdx);
              setStepStates((prev) => ({
                ...prev,
                [stepIdx]: {
                  ...prev[stepIdx],
                  status: "running",
                },
              }));
              setLogs((prev) => [
                ...prev,
                `[Step ${stepIdx + 1}/${currentPipeline.steps.length}] ${parsed.step_name} (${parsed.persona}) starting...`,
              ]);
            } else if (eventName === "step_token") {
              const stepIdx = parsed.step_index;
              const token = parsed.token;
              setStepStates((prev) => {
                const current = prev[stepIdx];
                if (!current) return prev;
                return {
                  ...prev,
                  [stepIdx]: {
                    ...current,
                    tokens: [...current.tokens, token],
                  },
                };
              });
            } else if (eventName === "step_complete") {
              const stepIdx = parsed.step_index;
              setStepStates((prev) => ({
                ...prev,
                [stepIdx]: {
                  ...prev[stepIdx],
                  status: "completed",
                  output: parsed.output,
                  duration_ms: parsed.duration_ms,
                },
              }));
              setLogs((prev) => [
                ...prev,
                `[Step ${stepIdx + 1} Completed] Duration: ${parsed.duration_ms}ms`,
              ]);
            } else if (eventName === "step_failed") {
              const stepIdx = parsed.step_index;
              setStepStates((prev) => ({
                ...prev,
                [stepIdx]: {
                  ...prev[stepIdx],
                  status: "failed",
                  error: parsed.error,
                  duration_ms: parsed.duration_ms,
                },
              }));
              setLogs((prev) => [
                ...prev,
                `[Step ${stepIdx + 1} FAILED] Error: ${parsed.error}`,
              ]);
            } else if (eventName === "pipeline_complete") {
              setFinalOutput(parsed.final_output || "");
              setTotalDurationMs(parsed.total_duration_ms || 0);
              setActiveStepIndex(null);
              setLogs((prev) => [
                ...prev,
                `[Pipeline Result] Status: ${parsed.status} | Total Duration: ${parsed.total_duration_ms}ms`,
              ]);
            }
          } catch {
            // Ignore parse errors on partial frames
          }
        }
      }
    } catch (err: unknown) {
      if ((err as Error).name !== "AbortError") {
        const errorMsg = err instanceof Error ? err.message : String(err);
        setLogs((prev) => [...prev, `[Execution Error] ${errorMsg}`]);
      }
    } finally {
      setIsExecuting(false);
      abortControllerRef.current = null;
    }
  };

  const handleStopPipeline = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsExecuting(false);
      setLogs((prev) => [...prev, "[System] Pipeline execution cancelled by user."]);
    }
  };

  const handleCopyOutput = () => {
    if (!finalOutput) return;
    navigator.clipboard.writeText(finalOutput);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-fg tracking-tight flex items-center gap-2">
            <Workflow className="h-5 w-5 text-hue-cyan" aria-hidden="true" />
            Live Multi-Agent Pipeline &amp; DAG Visualizer
          </h3>
          <p className="text-xs text-fg-3 mt-0.5">
            Distributed execution across networked Gateway instances with real-time SSE stage telemetry
          </p>
        </div>

        {runId && (
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="px-3 py-1 rounded-full bg-panel border border-line text-hue-cyan">
              Run: {runId}
            </span>
            {totalDurationMs !== null && (
              <span className="px-3 py-1 rounded-full bg-panel border border-line text-hue-emerald">
                {totalDurationMs} ms
              </span>
            )}
          </div>
        )}
      </div>

      {/* Pipeline Selector Bar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-line pb-3">
        {DEFAULT_PIPELINES.map((p) => {
          const isSelected = p.name === selectedPipelineName;
          return (
            <button
              key={p.name}
              type="button"
              disabled={isExecuting}
              onClick={() => setSelectedPipelineName(p.name)}
              className={`px-4 py-2 rounded-xl text-xs font-mono border transition-all flex items-center gap-2 ${
                isSelected
                  ? "bg-hue-cyan-tint/60 text-hue-cyan border-hue-cyan-line/60 shadow-xs"
                  : "bg-panel/50 text-fg-3 border-line hover:border-line-strong hover:text-fg"
              } ${isExecuting ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            >
              <Layers className="h-3.5 w-3.5" aria-hidden="true" />
              <span className="font-semibold">{p.name}</span>
              <span className="text-[10px] opacity-75">({p.steps_count} steps)</span>
            </button>
          );
        })}
      </div>

      {/* Interactive SVG DAG Canvas */}
      <div className="p-6 rounded-2xl bg-panel border border-line/80 shadow-xs relative overflow-hidden">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-xs font-mono text-fg-2">
            <Sparkles className="h-4 w-4 text-hue-cyan" aria-hidden="true" />
            <span>Interactive Stage DAG: <strong>{currentPipeline.name}</strong></span>
          </div>
          <span className="text-[11px] text-fg-3 font-mono">
            {currentPipeline.description}
          </span>
        </div>

        {/* Node Link Cards Container */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center relative py-4">
          {currentPipeline.steps.map((step, idx) => {
            const state = stepStates[idx] || {
              status: "idle",
              output: "",
              tokens: [],
            };
            const personaStyle = PERSONA_COLORS[step.persona] || PERSONA_COLORS.sakthai;
            const isRunning = state.status === "running";
            const isCompleted = state.status === "completed";
            const isFailed = state.status === "failed";

            return (
              <React.Fragment key={step.name}>
                {/* Stage Node Box */}
                <div
                  className={`relative p-5 rounded-xl border transition-all duration-300 flex flex-col justify-between min-h-[170px] ${
                    isRunning
                      ? `bg-panel border-hue-cyan shadow-md ring-2 ring-hue-cyan/40 scale-[1.02] ${personaStyle.glow}`
                      : isCompleted
                      ? "bg-panel/90 border-emerald-500/50 shadow-xs"
                      : isFailed
                      ? "bg-panel/90 border-rose-500/50 shadow-xs"
                      : "bg-panel/40 border-line text-fg-3"
                  }`}
                >
                  {/* Step Header */}
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-mono text-fg-3 font-semibold">
                      Step 0{idx + 1}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full border uppercase tracking-wider font-bold ${personaStyle.bg} ${personaStyle.text} ${personaStyle.border}`}
                    >
                      {step.persona}
                    </span>
                  </div>

                  {/* Stage Title */}
                  <div className="my-2">
                    <h4 className="text-sm font-bold font-display text-fg tracking-tight">
                      {step.name}
                    </h4>
                    <p className="text-[11px] font-mono text-fg-3 mt-1 truncate">
                      Key: <code className="text-fg-2">{step.output_key}</code>
                    </p>
                  </div>

                  {/* Status Indicator */}
                  <div className="flex items-center justify-between pt-2 border-t border-line/60 text-xs font-mono">
                    <div className="flex items-center gap-1.5">
                      {isRunning && (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin text-hue-cyan" />
                          <span className="text-hue-cyan font-bold">Running</span>
                        </>
                      )}
                      {isCompleted && (
                        <>
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                          <span className="text-emerald-400 font-bold">Done</span>
                        </>
                      )}
                      {isFailed && (
                        <>
                          <AlertCircle className="h-3.5 w-3.5 text-rose-400" />
                          <span className="text-rose-400 font-bold">Failed</span>
                        </>
                      )}
                      {!isRunning && !isCompleted && !isFailed && (
                        <>
                          <div className="h-2 w-2 rounded-full bg-line-strong" />
                          <span className="text-fg-3">Idle</span>
                        </>
                      )}
                    </div>

                    {state.duration_ms !== undefined && (
                      <span className="text-[10px] text-fg-3 flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {state.duration_ms}ms
                      </span>
                    )}
                  </div>
                </div>

                {/* Arrow Connector between steps */}
                {idx < currentPipeline.steps.length - 1 && (
                  <div className="hidden md:flex justify-center items-center text-line-strong absolute" style={{ left: `${(idx + 1) * 33.33 - 2}%`, zIndex: 10 }}>
                    <div className="p-1.5 rounded-full bg-canvas border border-line shadow-xs">
                      <ArrowRight className="h-4 w-4 text-hue-cyan/70" />
                    </div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Task Dispatch & Interactive Controls */}
      <div className="p-5 rounded-2xl bg-panel border border-line shadow-xs space-y-4">
        <label htmlFor="pipeline-task-input" className="block text-xs font-mono text-fg-2 font-semibold">
          Execution Task Prompt:
        </label>
        <textarea
          id="pipeline-task-input"
          rows={3}
          value={taskPrompt}
          disabled={isExecuting}
          onChange={(e) => setTaskPrompt(e.target.value)}
          placeholder="Enter prompt instruction to dispatch across the multi-agent pipeline..."
          className="w-full px-4 py-3 rounded-xl bg-canvas border border-line text-xs font-mono text-fg placeholder:text-fg-3 focus:outline-hidden focus:border-hue-cyan focus:ring-1 focus:ring-hue-cyan"
        />

        <div className="flex items-center justify-between gap-4">
          <div className="text-[11px] text-fg-3 font-mono">
            {isExecuting ? (
              <span className="flex items-center gap-1.5 text-hue-cyan">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Live streaming SSE pipeline execution...
              </span>
            ) : (
              <span>Ready to stream pipeline through Gateway (:8080)</span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {isExecuting ? (
              <button
                type="button"
                onClick={handleStopPipeline}
                className="px-4 py-2 rounded-xl text-xs font-mono bg-rose-500/20 text-rose-300 border border-rose-500/40 hover:bg-rose-500/30 transition-colors flex items-center gap-1.5 cursor-pointer font-bold"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Cancel
              </button>
            ) : (
              <button
                type="button"
                onClick={handleStartPipeline}
                disabled={!taskPrompt.trim()}
                className="px-5 py-2.5 rounded-xl text-xs font-mono bg-hue-cyan-tint/70 text-hue-cyan border border-hue-cyan-line hover:bg-hue-cyan-tint hover:border-hue-cyan transition-all flex items-center gap-2 cursor-pointer font-bold shadow-xs disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="h-3.5 w-3.5 fill-current" />
                Execute Live Pipeline
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Terminal Drawer & Real-Time Token Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Terminal Logs Box */}
        <div className="p-4 rounded-2xl bg-canvas border border-line font-mono text-xs shadow-inner flex flex-col h-[280px]">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-line text-fg-3">
            <span className="flex items-center gap-1.5 text-hue-cyan font-bold">
              <Terminal className="h-3.5 w-3.5" />
              Live SSE Pipeline Stream
            </span>
            <span className="text-[10px]">{logs.length} events logged</span>
          </div>
          <div ref={terminalRef} className="flex-1 overflow-y-auto space-y-1 text-fg-2 text-[11px] leading-relaxed">
            {logs.length === 0 ? (
              <div className="text-fg-3/60 italic py-8 text-center">
                Execution events and streamed stage tokens will appear here...
              </div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="whitespace-pre-wrap">
                  {log}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Final Synthesized Output Box */}
        <div className="p-4 rounded-2xl bg-panel border border-line font-mono text-xs shadow-xs flex flex-col h-[280px]">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-line text-fg-3">
            <span className="flex items-center gap-1.5 text-hue-emerald font-bold">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Final Pipeline Synthesis
            </span>
            {finalOutput && (
              <button
                type="button"
                onClick={handleCopyOutput}
                className="text-[10px] text-fg-2 hover:text-fg flex items-center gap-1 px-2 py-0.5 rounded border border-line hover:border-line-strong cursor-pointer"
              >
                {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                {copied ? "Copied!" : "Copy"}
              </button>
            )}
          </div>
          <div className="flex-1 overflow-y-auto text-fg text-[11px] leading-relaxed whitespace-pre-wrap">
            {finalOutput ? (
              finalOutput
            ) : (
              <div className="text-fg-3/60 italic py-8 text-center">
                {isExecuting ? "Synthesizing output across pipeline stages..." : "No final output yet. Click 'Execute Live Pipeline' to start."}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
