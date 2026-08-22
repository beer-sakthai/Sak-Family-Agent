"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Zap,
  Activity,
  Power,
  RefreshCw,
} from "lucide-react";
import { IncidentRecord, PersonaHealthSummary } from "@/lib/selfHealingEngine";
import { usePanelFetch } from "@/lib/hooks/usePanelFetch";

interface RecoveryResponse {
  success: boolean;
  data?: {
    health: PersonaHealthSummary[];
    incidents: IncidentRecord[];
    timestamp: string;
  };
}

export function SelfHealingConsole() {
  const { data: recoveryData, loading: fetchLoading, refresh } = usePanelFetch<RecoveryResponse>(
    "/api/recovery",
    { pollIntervalMs: 10_000 },
  );

  const healthList = recoveryData?.data?.health ?? [];
  const incidents = recoveryData?.data?.incidents ?? [];

  const [actionLoading, setActionLoading] = useState(false);
  const [replayingId, setReplayingId] = useState<string | null>(null);

  const handleReplay = async (id: string) => {
    setReplayingId(id);
    try {
      const res = await fetch("/api/recovery", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "replay", id }),
      });
      const data = await res.json();
      if (data.success) {
        await refresh();
      }
    } catch (err) {
      console.error("Replay failed", err);
    } finally {
      setReplayingId(null);
    }
  };

  const handleResetCircuit = async (persona: string) => {
    setActionLoading(true);
    try {
      await fetch("/api/recovery", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "reset_circuit", persona }),
      });
      await refresh();
    } catch (err) {
      console.error("Reset circuit failed", err);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-rose-400" />
            Self-Healing Multi-Agent Recovery Protocol
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800/60 font-semibold">
              Autonomous v1.0
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
            Active telemetry for circuit-breaker thresholds, Dead-Letter Queue (DLQ) automated replay, and zero-downtime agent failover consensus.
          </p>
        </div>
        <button
          onClick={() => refresh()}
          disabled={fetchLoading || actionLoading}
          aria-label="Refresh recovery telemetry state"
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-300 border border-slate-700 transition-colors focus-visible:ring-2 focus-visible:ring-rose-400 focus:outline-none disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${fetchLoading ? "animate-spin text-rose-400" : ""}`} />
          Refresh State
        </button>
      </div>

      {/* Grid: Left Column (Health Matrix), Right Column (DLQ & Fallback Strategy) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Persona Circuit Breaker Matrix */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <Activity className="h-4 w-4 text-cyan-400" />
              Persona Circuit Breaker & Health State
            </h4>
            <span className="text-xs text-slate-400 font-mono">
              6 Agent Nodes Registered
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {healthList.map((item) => {
              const isClosed = item.circuitBreaker === "CLOSED";
              const isHalfOpen = item.circuitBreaker === "HALF-OPEN";
              const isOpen = item.circuitBreaker === "OPEN";

              return (
                <div
                  key={item.persona}
                  className={`p-4 rounded-xl border transition-all ${
                    isOpen
                      ? "bg-rose-950/30 border-rose-800/60 shadow-lg shadow-rose-950/20"
                      : isHalfOpen
                      ? "bg-amber-950/20 border-amber-800/50"
                      : "bg-slate-900/60 border-slate-800/80"
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2.5">
                      <span className="font-display font-semibold text-white text-sm">
                        {item.persona}
                      </span>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold uppercase ${
                          isOpen
                            ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                            : isHalfOpen
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                            : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                        }`}
                      >
                        {item.circuitBreaker}
                      </span>
                    </div>

                    {isOpen && (
                      <button
                        onClick={() => handleResetCircuit(item.persona)}
                        disabled={actionLoading}
                        aria-label={`Reset circuit breaker for ${item.persona}`}
                        className="text-[11px] font-mono flex items-center gap-1 text-rose-300 hover:text-white bg-rose-900/40 hover:bg-rose-800/60 px-2 py-1 rounded border border-rose-700/60 transition-colors focus-visible:ring-2 focus-visible:ring-rose-400 focus:outline-none disabled:opacity-50"
                      >
                        <Power className="h-3 w-3" />
                        Reset
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="bg-slate-950/50 p-2 rounded-lg border border-slate-800/60">
                      <div className="text-slate-400 text-[10px] uppercase">Failure Count</div>
                      <div
                        className={`text-base font-bold ${
                          item.failureCount > 0 ? "text-rose-400" : "text-slate-300"
                        }`}
                      >
                        {item.failureCount}
                        <span className="text-xs text-slate-400 font-normal"> / 3</span>
                      </div>
                    </div>
                    <div className="bg-slate-950/50 p-2 rounded-lg border border-slate-800/60">
                      <div className="text-slate-400 text-[10px] uppercase">Pending DLQ</div>
                      <div className="text-base font-bold text-cyan-300">
                        {item.pendingDlqCount}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right 1 Col: Dead-Letter Queue (DLQ) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <Zap className="h-4 w-4 text-amber-400" />
              Dead-Letter Queue (DLQ)
            </h4>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {incidents.filter((i) => i.status === "pending").length} pending
            </span>
          </div>

          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 space-y-3">
            {incidents.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-xs">
                <CheckCircle className="h-8 w-8 text-emerald-400/60 mx-auto mb-2" />
                No DLQ incidents logged. System healthy.
              </div>
            ) : (
              incidents.slice(0, 5).map((inc) => (
                <div
                  key={inc.id}
                  className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <span className="font-display font-semibold text-xs text-white">
                      {inc.persona}
                    </span>
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded uppercase font-semibold ${
                        inc.status === "replayed"
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                          : inc.status === "quarantined"
                          ? "bg-rose-950 text-rose-300 border border-rose-800"
                          : "bg-amber-950 text-amber-300 border border-amber-800"
                      }`}
                    >
                      {inc.status}
                    </span>
                  </div>

                  <p className="text-xs text-slate-400 line-clamp-1 mb-2 font-mono">
                    {inc.action}
                  </p>

                  <div className="text-[10px] text-rose-400/90 font-mono bg-rose-950/30 px-2 py-1 rounded border border-rose-900/30 mb-2">
                    {inc.errorMessage}
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-slate-800/60">
                    <span className="text-[10px] font-mono text-slate-400">
                      Attempts: {inc.retryCount} / {inc.maxRetries}
                    </span>

                    {inc.status === "pending" && (
                      <button
                        onClick={() => handleReplay(inc.id)}
                        disabled={replayingId === inc.id}
                        aria-label={`Replay DLQ incident ${inc.id} for ${inc.persona}`}
                        className="text-[11px] font-mono flex items-center gap-1 text-cyan-300 hover:text-white bg-cyan-950 hover:bg-cyan-900 px-2 py-0.5 rounded border border-cyan-800/60 transition-colors focus-visible:ring-2 focus-visible:ring-cyan-400 focus:outline-none disabled:opacity-50"
                      >
                        <RotateCcw
                          className={`h-3 w-3 ${
                            replayingId === inc.id ? "animate-spin text-cyan-300" : ""
                          }`}
                        />
                        Replay
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
