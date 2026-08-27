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
      {/* No title here: the topbar names the section and repeats this exact
          description. What is left is the two counts, which it does not. */}
      <div className="flex items-center justify-end flex-wrap gap-2">
        <div className="flex items-center gap-2">
          {/* Runs recorded before persona attribution existed. Shown plainly
              rather than distributed across the personas, which is what the
              old round-robin heuristic did. */}
          {unattributed > 0 && (
            <div
              className="text-xs font-mono text-hue-amber bg-hue-amber-tint/30 border border-hue-amber-line/40 px-3 py-1 rounded-full"
              title="Runs recorded before persona attribution existed. Not assigned to any persona."
            >
              {unattributed} unattributed
            </div>
          )}
          <div className="text-xs font-mono text-hue-cyan bg-hue-cyan-tint/40 border border-hue-cyan-line/40 px-3 py-1 rounded-full">
            {agents.length} Personas Registered
          </div>
        </div>
      </div>

      {/* Auto-fill rather than a fixed column count at each breakpoint: the
          sidebar takes 248px of the viewport and can be collapsed at any time,
          so a card's width does not follow from the breakpoint. A 17rem floor
          fits the name, the provider badge and the status pill on one line;
          six fixed columns did not, and squeezed the name out entirely. */}
      <div className="grid gap-4 grid-cols-[repeat(auto-fill,minmax(min(100%,17rem),1fr))]">
        {agents.map((agent) => (
          <AgentCard key={agent.name} agent={agent} />
        ))}
      </div>
    </div>
  );
}

export default AgentOverview;
