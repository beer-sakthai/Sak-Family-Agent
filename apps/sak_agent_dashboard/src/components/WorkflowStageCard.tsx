"use client";

import React from "react";
import { Check, GitBranch, Sliders, FileJson, Layers } from "lucide-react";
import { WorkflowStage } from "@/lib/types";
import { getPersonaTheme } from "@/lib/uiUtils";

interface WorkflowStageCardProps {
  stage: WorkflowStage;
  index: number;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

export function WorkflowStageCard({
  stage,
  index,
  isExpanded = false,
  onToggleExpand,
}: WorkflowStageCardProps) {
  const theme = getPersonaTheme(stage.personaSlug);
  const hasDependencies = stage.dependsOn && stage.dependsOn.length > 0;

  return (
    <div
      onClick={onToggleExpand}
      className={`p-5 rounded-2xl bg-slate-900/80 border transition-all flex flex-col justify-between space-y-3 relative group ${
        onToggleExpand ? "cursor-pointer" : ""
      } ${
        isExpanded
          ? "border-cyan-500/50 shadow-lg shadow-cyan-950/30"
          : "border-slate-800/80 hover:border-slate-700/80"
      }`}
    >
      {/* Step Index & Persona Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="h-6 w-6 rounded-full bg-slate-800 border border-slate-700 text-[11px] font-bold font-mono text-cyan-400 flex items-center justify-center">
            {index + 1}
          </span>
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${theme.badge}`}>
            {stage.personaName}
          </span>
        </div>

        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold border ${
            stage.status === "completed"
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
              : stage.status === "running"
              ? "bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse"
              : stage.status === "failed"
              ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
              : "bg-slate-800 text-slate-400 border-slate-700"
          }`}
        >
          {stage.status === "completed" && <Check className="h-3 w-3" />}
          {stage.status.toUpperCase()}
        </span>
      </div>

      {/* Stage Name & Action */}
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

      {/* Expanded Parameters / State Output Drawer */}
      {isExpanded && (
        <div className="mt-2 pt-3 border-t border-slate-800 space-y-2 text-[11px] font-mono">
          {stage.params && Object.keys(stage.params).length > 0 && (
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
        <span className="text-cyan-400 font-semibold">{stage.provider.toUpperCase()}</span>
        <span>{stage.model}</span>
      </div>
    </div>
  );
}
