"use client";

import React, { useState } from "react";
import {
  Workflow,
  Play,
  CheckCircle2,
  Clock,
  Zap,
  ArrowRight,
  Shield,
  Layers,
  Sparkles,
  Terminal,
  Activity,
  Check,
} from "lucide-react";
import { WORKFLOW_TOPOLOGIES } from "@/lib/workflowEngine";
import { WorkflowTopology, WorkflowStage } from "@/lib/types";

const personaBadgeColors: Record<string, string> = {
  sakthai: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
  sakking: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  saksee: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  saksit: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  sakjules: "bg-rose-500/10 text-rose-400 border-rose-500/30",
  saktan: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
};

export function WorkflowFrameworkPanel() {
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowTopology>(WORKFLOW_TOPOLOGIES[0]);
  const [isRunning, setIsRunning] = useState(false);
  const [activeStages, setActiveStages] = useState<WorkflowStage[]>(WORKFLOW_TOPOLOGIES[0].stages);
  const [lastExecutionStats, setLastExecutionStats] = useState<{
    tokens: number;
    durationMs: number;
    executionId: string;
  } | null>(null);

  const handleSelectWorkflow = (wf: WorkflowTopology) => {
    setSelectedWorkflow(wf);
    setActiveStages(wf.stages);
    setLastExecutionStats(null);
  };

  const handleRunWorkflow = async () => {
    setIsRunning(true);
    try {
      const res = await fetch("/api/workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workflowId: selectedWorkflow.id }),
      });
      const data = await res.json();
      if (data.success && data.result) {
        setActiveStages(data.result.stages);
        setLastExecutionStats({
          tokens: data.result.totalTokens,
          durationMs: data.result.totalLatencyMs,
          executionId: data.result.executionId,
        });
      }
    } catch (err) {
      console.error("Workflow trigger failed", err);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Workflow className="h-5 w-5 text-cyan-400" />
            6-Agent Collaborative Workflow Framework
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/60 font-semibold">
              Orchestrator v2.0
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
            Multi-agent pipeline framework orchestrating SakThai, SakKing, SakSee, SakSit, SakJules, and SakTan across specialized domain stages with automated fallback routing and real-time SSE telemetry.
          </p>
        </div>

        <button
          onClick={handleRunWorkflow}
          disabled={isRunning}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-950/50 transition-all disabled:opacity-50"
        >
          <Play className={`h-4 w-4 fill-current ${isRunning ? "animate-spin" : ""}`} />
          <span>{isRunning ? "Executing Pipeline..." : "Trigger Autonomous Pipeline"}</span>
        </button>
      </div>

      {/* Workflow Topology Selector Tabs */}
      <div className="flex flex-wrap items-center gap-2 p-1.5 rounded-xl bg-slate-900/90 border border-slate-800/80">
        {WORKFLOW_TOPOLOGIES.map((wf) => (
          <button
            key={wf.id}
            onClick={() => handleSelectWorkflow(wf)}
            className={`px-4 py-2 rounded-lg text-xs font-semibold font-mono transition-all ${
              selectedWorkflow.id === wf.id
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-md shadow-cyan-950/40"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            {wf.name}
          </button>
        ))}
      </div>

      {/* Workflow Execution Stats Banner if available */}
      {lastExecutionStats && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-emerald-300">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>
              Pipeline Execution Successful (ID: <strong>{lastExecutionStats.executionId}</strong>)
            </span>
          </div>
          <div className="flex items-center space-x-4 text-slate-300">
            <span>⚡ Tokens: <strong>+{lastExecutionStats.tokens}</strong></span>
            <span>⏱️ Total Latency: <strong>{lastExecutionStats.durationMs}ms</strong></span>
          </div>
        </div>
      )}

      {/* Visual Pipeline DAG Stages */}
      <div className="space-y-3">
        <h4 className="text-sm font-bold text-slate-300 font-mono flex items-center gap-2">
          <Layers className="h-4 w-4 text-cyan-400" />
          Pipeline Stages & Cross-Agent Handoffs ({activeStages.length} Stages)
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {activeStages.map((stage, idx) => {
            const badgeColor = personaBadgeColors[stage.personaSlug.toLowerCase()] || "bg-slate-800 text-slate-300";

            return (
              <div
                key={stage.id}
                className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 hover:border-slate-700/80 transition-all flex flex-col justify-between space-y-3 relative group"
              >
                {/* Step Index Badge */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="h-6 w-6 rounded-full bg-slate-800 border border-slate-700 text-[11px] font-bold font-mono text-cyan-400 flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${badgeColor}`}>
                      {stage.personaName}
                    </span>
                  </div>

                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold border ${
                      stage.status === "completed"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                        : "bg-slate-800 text-slate-400 border-slate-700"
                    }`}
                  >
                    {stage.status === "completed" && <Check className="h-3 w-3" />}
                    {stage.status.toUpperCase()}
                  </span>
                </div>

                {/* Stage Title & Action */}
                <div>
                  <h5 className="text-xs font-bold text-white tracking-tight">{stage.name}</h5>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{stage.action}</p>
                </div>

                {/* Provider & Model Footer */}
                <div className="pt-2 border-t border-slate-800/70 flex items-center justify-between text-[10px] font-mono text-slate-500">
                  <span className="text-cyan-400">{stage.provider.toUpperCase()}</span>
                  <span>{stage.model}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
