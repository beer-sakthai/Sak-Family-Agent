"use client";

import React, { useState } from "react";
import {
  Activity,
  Radio,
  Pause,
  Play,
  Trash2,
  ShieldAlert,
  Wrench,
  Sparkles,
  Zap,
  Terminal,
  Clock,
} from "lucide-react";
import { useAgentStream } from "@/lib/hooks/useAgentStream";
import { TelemetryEventType } from "@/lib/types";
import { formatLatency, formatTokenCount } from "@/lib/uiUtils";

const eventBadgeStyles: Record<
  TelemetryEventType,
  { bg: string; text: string; icon: React.ReactNode }
> = {
  connected: {
    bg: "bg-emerald-500/10 border-emerald-500/30",
    text: "text-emerald-400",
    icon: <Radio className="h-3.5 w-3.5" />,
  },
  agent_start: {
    bg: "bg-cyan-500/10 border-cyan-500/30",
    text: "text-cyan-400",
    icon: <Zap className="h-3.5 w-3.5" />,
  },
  agent_message: {
    bg: "bg-cyan-500/10 border-cyan-500/30",
    text: "text-cyan-400",
    icon: <Zap className="h-3.5 w-3.5" />,
  },
  agent_dispatch: {
    bg: "bg-teal-500/10 border-teal-500/30",
    text: "text-teal-400",
    icon: <Zap className="h-3.5 w-3.5" />,
  },
  agent_step: {
    bg: "bg-sky-500/10 border-sky-500/30",
    text: "text-sky-400",
    icon: <Activity className="h-3.5 w-3.5" />,
  },
  token_delta: {
    bg: "bg-indigo-500/10 border-indigo-500/30",
    text: "text-indigo-400",
    icon: <Sparkles className="h-3.5 w-3.5" />,
  },
  tool_call: {
    bg: "bg-amber-500/10 border-amber-500/30",
    text: "text-amber-400",
    icon: <Wrench className="h-3.5 w-3.5" />,
  },
  tool_result: {
    bg: "bg-purple-500/10 border-purple-500/30",
    text: "text-purple-400",
    icon: <Terminal className="h-3.5 w-3.5" />,
  },
  guardrail_check: {
    bg: "bg-rose-500/10 border-rose-500/30",
    text: "text-rose-400",
    icon: <ShieldAlert className="h-3.5 w-3.5" />,
  },
  memory_mutation: {
    bg: "bg-blue-500/10 border-blue-500/30",
    text: "text-blue-400",
    icon: <Activity className="h-3.5 w-3.5" />,
  },
  agent_complete: {
    bg: "bg-emerald-500/10 border-emerald-500/30",
    text: "text-emerald-400",
    icon: <Clock className="h-3.5 w-3.5" />,
  },
  agent_error: {
    bg: "bg-red-500/20 border-red-500/40",
    text: "text-red-400",
    icon: <ShieldAlert className="h-3.5 w-3.5" />,
  },
  heartbeat: {
    bg: "bg-slate-500/10 border-slate-500/30",
    text: "text-slate-400",
    icon: <Activity className="h-3.5 w-3.5" />,
  },
};

const ALL_PERSONAS = [
  "SakThai",
  "SakKing",
  "SakSee",
  "SakSit",
  "SakJules",
  "SakTan",
];

export function LiveTelemetryFeed() {
  const [selectedPersona, setSelectedPersona] = useState<string>("");
  const [isPaused, setIsPaused] = useState(false);

  const { status, events, clearEvents, connect, disconnect } = useAgentStream({
    persona: selectedPersona || undefined,
    autoConnect: !isPaused,
    maxEvents: 50,
  });

  const togglePause = () => {
    if (isPaused) {
      connect();
      setIsPaused(false);
    } else {
      disconnect();
      setIsPaused(true);
    }
  };

  return (
    <div className="glass-card rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl p-5 shadow-2xl space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <Radio
              className={`h-5 w-5 ${status === "connected" ? "animate-pulse" : ""}`}
            />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              Real-Time Agent Telemetry Stream
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
                  status === "connected"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : status === "connecting"
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse"
                    : "bg-slate-500/10 text-slate-400 border-slate-500/30"
                }`}
              >
                {status.toUpperCase()}
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Zero-latency Server-Sent Events (SSE) trace pipeline
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Persona Filter */}
          <select
            value={selectedPersona}
            onChange={(e) => setSelectedPersona(e.target.value)}
            aria-label="Filter by Persona"
            className="bg-slate-800 text-slate-300 text-xs rounded-lg px-3 py-1.5 border border-slate-700 focus:outline-none focus:border-cyan-500 focus-visible:ring-2 focus-visible:ring-cyan-500"
          >
            <option value="">All Personas</option>
            {ALL_PERSONAS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>

          {/* Pause / Resume Button */}
          <button
            onClick={togglePause}
            aria-label={isPaused ? "Resume stream" : "Pause stream"}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs border border-slate-700 transition-colors focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:outline-none"
          >
            {isPaused ? (
              <Play className="h-3.5 w-3.5 text-emerald-400" />
            ) : (
              <Pause className="h-3.5 w-3.5 text-amber-400" />
            )}
            <span>{isPaused ? "Resume" : "Pause"}</span>
          </button>

          {/* Clear Feed */}
          <button
            onClick={clearEvents}
            disabled={events.length === 0}
            aria-label="Clear stream events"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-400 hover:text-rose-400 border border-slate-700 transition-colors focus-visible:ring-2 focus-visible:ring-rose-500 focus-visible:outline-none"
            title={events.length === 0 ? "Stream is empty" : "Clear stream events"}
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Stream Event List */}
      <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
        {events.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl">
            <Radio className="h-8 w-8 text-slate-600 mx-auto mb-2 animate-pulse" />
            <p className="text-xs text-slate-400 font-medium">
              Listening for live agent execution telemetry...
            </p>
            <p className="text-[11px] text-slate-500 mt-1">
              Events will appear here in real-time as agents trigger tasks
            </p>
          </div>
        ) : (
          events.map((evt) => {
            const style =
              eventBadgeStyles[evt.type] || eventBadgeStyles.heartbeat;
            return (
              <div
                key={evt.id}
                className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700/80 transition-all flex flex-col space-y-1.5 text-xs font-mono"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[11px] font-semibold ${style.bg} ${style.text}`}
                    >
                      {style.icon}
                      {evt.type.toUpperCase()}
                    </span>
                    <span className="font-semibold text-slate-200">
                      {evt.persona}
                    </span>
                    {evt.sessionId && (
                      <span className="text-[10px] text-slate-500 font-normal">
                        ({evt.sessionId.slice(0, 8)})
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-500">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                {/* Event Message or Detail Payload */}
                <div className="text-slate-300 text-[11px] pl-1">
                  {evt.data.message && <span>{evt.data.message}</span>}
                  {evt.data.toolName && (
                    <div className="text-amber-300">
                      🔧 Tool Invoked:{" "}
                      <span className="font-bold">{evt.data.toolName}</span>
                    </div>
                  )}
                  {evt.data.guardrailRule && (
                    <div className="text-rose-300">
                      🛡️ Guardrail ({evt.data.guardrailAction}):{" "}
                      {evt.data.guardrailRule}
                    </div>
                  )}
                  {evt.data.tokensGenerated && (
                    <div className="text-indigo-300">
                      ⚡ Tokens: +{formatTokenCount(evt.data.tokensGenerated)} (
                      {formatLatency(evt.data.latencyMs)})
                    </div>
                  )}
                  {evt.data.error && (
                    <div className="text-red-400 font-semibold">
                      ⚠️ Error: {evt.data.error}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
