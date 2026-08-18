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
  GitBranch,
  RefreshCw,
  Sliders,
  Code2,
  FileJson,
  CheckCircle,
} from "lucide-react";
import { WORKFLOW_TOPOLOGIES, validateWorkflowDAG, buildTopologicalBatches } from "@/lib/workflowEngine";
import { WorkflowTopology, WorkflowStage, WorkflowRunHistory } from "@/lib/types";

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
  const [expandedStepId, setExpandedStepId] = useState<string | null>(null);
  const [lastExecutionStats, setLastExecutionStats] = useState<{
    tokens: number;
    durationMs: number;
    executionId: string;
    topologicalOrder?: string[];
  } | null>(null);

  const dagValidation = validateWorkflowDAG(selectedWorkflow);
  const batches = dagValidation.isValid ? buildTopologicalBatches(selectedWorkflow) : [];

  const handleSelectWorkflow = (wf: WorkflowTopology) => {
    setSelectedWorkflow(wf);
    setActiveStages(wf.stages);
    setLastExecutionStats(null);
    setExpandedStepId(null);
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
          topologicalOrder: data.result.dagTopologicalOrder,
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
              DAG Engine v2.0
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
            Multi-agent pipeline framework orchestrating SakThai, SakKing, SakSee, SakSit, SakJules, and SakTan across topological DAG stages with automated dependency resolution, state interpolation, and real-time telemetry.
          </p>
        </div>

        <button
          onClick={handleRunWorkflow}
          disabled={isRunning || !dagValidation.isValid}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-950/50 transition-all disabled:opacity-50"
        >
          <Play className={`h-4 w-4 fill-current ${isRunning ? "animate-spin" : ""}`} />
          <span>{isRunning ? "Executing DAG Pipeline..." : "Trigger DAG Pipeline"}</span>
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

      {/* DAG Topology & Validation Indicator */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center space-x-2">
          {dagValidation.isValid ? (
            <span className="inline-flex items-center gap-1 text-emerald-400">
              <CheckCircle className="h-4 w-4" />
              <span>Valid DAG Graph (Kahn Topological Sort)</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-rose-400">
              <Shield className="h-4 w-4" />
              <span>Invalid DAG: {dagValidation.errors.join(", ")}</span>
            </span>
          )}
        </div>
        <div className="flex items-center space-x-3 text-slate-400 text-[11px]">
          <span>Stages: <strong className="text-white">{selectedWorkflow.stages.length}</strong></span>
          <span>•</span>
          <span>Parallel Batches: <strong className="text-cyan-300">{batches.length}</strong></span>
          <span>•</span>
          <span>Category: <span className="capitalize text-slate-300">{selectedWorkflow.category}</span></span>
        </div>
      </div>

      {/* Workflow Execution Stats Banner if available */}
      {lastExecutionStats && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-emerald-300">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>
              DAG Pipeline Execution Succeeded (ID: <strong>{lastExecutionStats.executionId}</strong>)
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
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-bold text-slate-300 font-mono flex items-center gap-2">
            <Layers className="h-4 w-4 text-cyan-400" />
            Pipeline DAG Stages & Cross-Agent Handoffs ({activeStages.length} Stages)
          </h4>
          <span className="text-[11px] font-mono text-slate-400">
            Click step card to inspect state inputs & outputs
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {activeStages.map((stage, idx) => {
            const badgeColor = personaBadgeColors[stage.personaSlug.toLowerCase()] || "bg-slate-800 text-slate-300";
            const isExpanded = expandedStepId === stage.id;
            const hasDependencies = stage.dependsOn && stage.dependsOn.length > 0;

            return (
              <div
                key={stage.id}
                onClick={() => setExpandedStepId(isExpanded ? null : stage.id)}
                className={`p-5 rounded-2xl bg-slate-900/80 border transition-all cursor-pointer flex flex-col justify-between space-y-3 relative group ${
                  isExpanded
                    ? "border-cyan-500/50 shadow-lg shadow-cyan-950/30"
                    : "border-slate-800/80 hover:border-slate-700/80"
                }`}
              >
                {/* Step Index & Status Badge */}
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

                {/* DAG Dependencies Indicator */}
                {hasDependencies && (
                  <div className="flex items-center gap-1 text-[10px] font-mono text-slate-400 bg-slate-950/40 px-2 py-1 rounded-lg border border-slate-800/60">
                    <GitBranch className="h-3 w-3 text-cyan-400" />
                    <span>Depends on:</span>
                    <span className="text-cyan-300 font-semibold">{stage.dependsOn?.join(", ")}</span>
                  </div>
                )}

                {/* Expanded Details Drawer */}
                {isExpanded && (
                  <div className="mt-2 pt-3 border-t border-slate-800 space-y-2 text-[11px] font-mono">
                    {stage.params && (
                      <div>
                        <span className="text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1">
                          <Sliders className="h-3 w-3 text-cyan-400" /> Parameters
                        </span>
                        <pre className="mt-1 p-2 rounded bg-slate-950 text-slate-300 overflow-x-auto text-[10px]">
                          {JSON.stringify(stage.params, null, 2)}
                        </pre>
                      </div>
                    )}

                    {stage.output && (
                      <div>
                        <span className="text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1">
                          <FileJson className="h-3 w-3 text-emerald-400" /> State Output
                        </span>
                        <pre className="mt-1 p-2 rounded bg-slate-950 text-emerald-300 overflow-x-auto text-[10px]">
                          {JSON.stringify(stage.output, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}

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
