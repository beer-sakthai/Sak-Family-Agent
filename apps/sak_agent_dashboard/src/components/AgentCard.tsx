"use client";

import React from "react";
import { Cpu, Zap, Activity, Award, Shield, Eye, Terminal, Clock } from "lucide-react";
import { AgentPersona } from "@/lib/types";

interface AgentCardProps {
  agent: AgentPersona;
}

const personaIcons: Record<string, React.ReactNode> = {
  SakThai: <Terminal className="h-5 w-5 text-cyan-400" />,
  SakKing: <Zap className="h-5 w-5 text-purple-400" />,
  SakSee: <Eye className="h-5 w-5 text-amber-400" />,
  SakSit: <Shield className="h-5 w-5 text-emerald-400" />,
  SakJules: <Activity className="h-5 w-5 text-rose-400" />,
};

const personaGlows: Record<string, string> = {
  SakThai: "border-cyan-500/30 hover:border-cyan-500/60 shadow-cyan-950/40",
  SakKing: "border-purple-500/30 hover:border-purple-500/60 shadow-purple-950/40",
  SakSee: "border-amber-500/30 hover:border-amber-500/60 shadow-amber-950/40",
  SakSit: "border-emerald-500/30 hover:border-emerald-500/60 shadow-emerald-950/40",
  SakJules: "border-rose-500/30 hover:border-rose-500/60 shadow-rose-950/40",
};

export function AgentCard({ agent }: AgentCardProps) {
  const isOnline = agent.status === "Active" || agent.status === "Ready";
  const glowClass = personaGlows[agent.name] || "border-slate-800 hover:border-slate-700";
  const icon = personaIcons[agent.name] || <Cpu className="h-5 w-5 text-cyan-400" />;

  // Default benchmark score if not explicitly set
  const score = agent.benchmarkScore ?? 92.5;

  return (
    <div
      className={`glass-card p-5 rounded-2xl bg-slate-900/80 border backdrop-blur-xl shadow-xl transition-all duration-300 flex flex-col justify-between space-y-4 relative overflow-hidden group ${glowClass}`}
    >
      {/* Background ambient glow */}
      <div className="absolute -top-10 -right-10 w-32 h-32 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition-all duration-500 pointer-events-none" />

      {/* Card Header: Persona Icon, Name & Status Pulse */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-slate-800/80 border border-slate-700/50">
              {icon}
            </div>
            <div>
              <h4 className="text-lg font-bold font-display text-white tracking-tight flex items-center gap-2">
                {agent.name}
                {agent.badge && (
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/50">
                    {agent.badge}
                  </span>
                )}
              </h4>
              <p className="text-xs text-slate-400 line-clamp-2 mt-0.5 leading-snug">
                {agent.role}
              </p>
            </div>
          </div>

          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold font-mono border ${
              isOnline
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : agent.status === "Warning" || agent.status === "Alert"
                ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                : "bg-slate-800/80 text-slate-400 border-slate-700"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isOnline
                  ? "bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]"
                  : agent.status === "Warning" || agent.status === "Alert"
                  ? "bg-amber-400 animate-pulse"
                  : "bg-slate-500"
              }`}
            />
            {agent.status}
          </span>
        </div>

        {/* Model Badge */}
        <div className="mt-3 flex items-center gap-2">
          <span className="text-[11px] font-mono text-slate-300 px-2.5 py-1 rounded-md bg-slate-800/90 border border-slate-700/60 inline-flex items-center gap-1.5">
            <Cpu className="h-3 w-3 text-cyan-400" />
            {agent.model}
          </span>
        </div>
      </div>

      {/* Metrics Row: Latency & Total Runs */}
      <div className="grid grid-cols-2 gap-2 py-2 px-3 rounded-xl bg-slate-950/60 border border-slate-800/80 font-mono text-xs">
        <div>
          <span className="text-[10px] uppercase text-slate-400 block mb-0.5 flex items-center gap-1">
            <Clock className="h-3 w-3 text-cyan-400" /> Latency
          </span>
          <span className="font-bold text-cyan-300">{agent.latencyMs}ms</span>
        </div>
        <div>
          <span className="text-[10px] uppercase text-slate-400 block mb-0.5 flex items-center gap-1">
            <Activity className="h-3 w-3 text-emerald-400" /> Executions
          </span>
          <span className="font-bold text-emerald-300">{agent.runs} runs</span>
        </div>
      </div>

      {/* Benchmark Score Progress Bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-slate-400 text-[11px] flex items-center gap-1">
            <Award className="h-3 w-3 text-amber-400" /> Benchmark Score
          </span>
          <span className="font-bold text-emerald-400">{score.toFixed(1)}%</span>
        </div>
        <div className="h-2 w-full bg-slate-800/90 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 via-teal-400 to-emerald-400 rounded-full transition-all duration-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]"
            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
          />
        </div>
      </div>

      {/* Skills Tags */}
      {agent.skills && agent.skills.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {agent.skills.map((skill) => (
            <span
              key={skill}
              className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950/40 text-cyan-300 border border-cyan-800/30"
            >
              #{skill}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default AgentCard;
