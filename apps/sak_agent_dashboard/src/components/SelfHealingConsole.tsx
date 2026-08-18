"use client";

import React, { useState, useEffect, useCallback } from "react";
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

export function SelfHealingConsole() {
  const [healthList, setHealthList] = useState<PersonaHealthSummary[]>([]);
  const [incidents, setIncidents] = useState<IncidentRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [replayingId, setReplayingId] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/recovery");
      const json = await res.json();
      if (json.success && json.data) {
        setHealthList(json.data.health);
        setIncidents(json.data.incidents);
      }
    } catch (err) {
      console.error("Failed to fetch recovery status", err);
    }
  }, []);

  useEffect(() => {
    // The poll is declared inside the effect so the state updates happen in an
    // async continuation rather than synchronously in the effect body, which is
    // what `react-hooks/set-state-in-effect` (React Compiler) requires.
    async function pollStatus() {
      await fetchStatus();
    }

    pollStatus();
    const interval = setInterval(pollStatus, 10_000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

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
        setIncidents((prev) =>
          prev.map((item) =>
            item.id === id ? { ...item, status: "replayed" } : item
          )
        );
        fetchStatus();
      }
    } catch (err) {
      console.error("Replay failed", err);
    } finally {
      setReplayingId(null);
    }
  };

  const handleResetCircuit = async (persona: string) => {
    setLoading(true);
    try {
      await fetch("/api/recovery", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "reset_circuit", persona }),
      });
      fetchStatus();
    } catch (err) {
      console.error("Reset circuit failed", err);
    } finally {
      setLoading(false);
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
            Real-time anomaly interception, Dead-Letter Queue (DLQ) replay,
            circuit breaker quarantine, and memory state rollback across all 6
            personas.
          </p>
        </div>

        <button
          onClick={fetchStatus}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* Persona Health Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {healthList.map((h) => {
          const isHealthy = h.status === "healthy";
          const isQuarantined = h.status === "quarantined";

          return (
            <div
              key={h.persona}
              className={`p-4 rounded-2xl border transition-all ${
                isHealthy
                  ? "bg-slate-900/70 border-slate-800"
                  : isQuarantined
                  ? "bg-rose-950/20 border-rose-800/60"
                  : "bg-amber-950/20 border-amber-800/60"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-white text-sm">
                    {h.persona}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase border ${
                      isHealthy
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                        : isQuarantined
                        ? "bg-rose-500/20 text-rose-400 border-rose-500/40 animate-pulse"
                        : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                    }`}
                  >
                    {h.status}
                  </span>
                </div>

                {!isHealthy && (
                  <button
                    onClick={() => handleResetCircuit(h.persona)}
                    disabled={loading}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 text-xs border border-slate-700 transition-colors"
                    title="Reset Circuit Breaker"
                  >
                    <Power className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>

              <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] font-mono">
                <div className="p-2 rounded-lg bg-slate-950/50 border border-slate-800/80">
                  <span className="text-slate-500 block">Circuit:</span>
                  <span
                    className={`font-semibold ${
                      h.circuitBreaker === "CLOSED"
                        ? "text-emerald-400"
                        : "text-rose-400"
                    }`}
                  >
                    {h.circuitBreaker}
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-slate-950/50 border border-slate-800/80">
                  <span className="text-slate-500 block">Pending DLQ:</span>
                  <span
                    className={`font-semibold ${
                      h.pendingDlqCount > 0
                        ? "text-rose-400"
                        : "text-slate-300"
                    }`}
                  >
                    {h.pendingDlqCount} items
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Dead-Letter Queue (DLQ) Feed */}
      <div className="glass-card rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl p-5 shadow-2xl space-y-4">
        <h4 className="text-sm font-bold text-slate-200 font-mono flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-400" />
          Dead-Letter Queue (DLQ) & Anomaly Inspector ({incidents.length} Envelopes)
        </h4>

        <div className="space-y-3">
          {incidents.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-xs font-mono">
              ✅ Zero active DLQ envelopes. All agent execution pipelines operating cleanly.
            </div>
          ) : (
            incidents.map((item) => (
              <div
                key={item.id}
                className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono text-xs"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded-md bg-slate-800 text-cyan-300 font-bold">
                      {item.persona}
                    </span>
                    <span className="font-semibold text-white">
                      {item.action}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
                        item.status === "replayed"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                          : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>
                  <p className="text-slate-400 text-[11px]">
                    <span className="text-rose-400 font-semibold">
                      [{item.errorType}]
                    </span>{" "}
                    {item.errorMessage}
                  </p>
                  <p className="text-slate-500 text-[10px]">
                    Retry Attempt: {item.retryCount}/{item.maxRetries} • Created:{" "}
                    {new Date(item.createdAt).toLocaleTimeString()}
                  </p>
                </div>

                {item.status === "pending" && (
                  <button
                    onClick={() => handleReplay(item.id)}
                    disabled={replayingId === item.id}
                    className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg font-bold text-xs bg-cyan-600 hover:bg-cyan-500 text-white transition-all disabled:opacity-50"
                  >
                    <RotateCcw
                      className={`h-3.5 w-3.5 ${
                        replayingId === item.id ? "animate-spin" : ""
                      }`}
                    />
                    <span>Replay Task</span>
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
