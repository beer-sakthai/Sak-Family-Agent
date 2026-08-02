"use client";

import React from "react";
import { AgentCard } from "./AgentCard";
import { AgentPersona } from "@/lib/types";

interface AgentOverviewProps {
  agents: AgentPersona[];
}

export function AgentOverview({ agents }: AgentOverviewProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight">
            Sak-Agent-Family Personas
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Active persona telemetry, status indicators, models, and performance benchmarks
          </p>
        </div>
        <div className="text-xs font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 px-3 py-1 rounded-full">
          {agents.length} Personas Registered
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {agents.map((agent) => (
          <AgentCard key={agent.name} agent={agent} />
        ))}
      </div>
    </div>
  );
}

export default AgentOverview;
