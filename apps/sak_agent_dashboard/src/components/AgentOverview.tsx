"use client";

import React from "react";

import type { PersonasPayload } from "@/lib/contracts.generated";
import { AgentCard } from "./AgentCard";

interface AgentOverviewProps {
  personas: PersonasPayload;
}

export function AgentOverview({ personas }: AgentOverviewProps) {
  const { personas: agents, unattributed_runs: unattributed } = personas;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight">
            Sak-Agent-Family Personas
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Per-persona activity, memory shards, and configured models
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Runs recorded before persona attribution existed. Shown plainly
              rather than distributed across the personas, which is what the
              old round-robin heuristic did. */}
          {unattributed > 0 && (
            <div
              className="text-xs font-mono text-amber-300 bg-amber-950/30 border border-amber-800/40 px-3 py-1 rounded-full"
              title="Runs recorded before persona attribution existed. Not assigned to any persona."
            >
              {unattributed} unattributed
            </div>
          )}
          <div className="text-xs font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 px-3 py-1 rounded-full">
            {agents.length} Personas Registered
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {agents.map((agent) => (
          <AgentCard key={agent.name} agent={agent} />
        ))}
      </div>
    </div>
  );
}

export default AgentOverview;
