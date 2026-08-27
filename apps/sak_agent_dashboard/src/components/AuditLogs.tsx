"use client";

import React from "react";
import { AlertTriangle, Info, Shield, ShieldAlert, ShieldCheck } from "lucide-react";

import type { AuditEvent, AuditPayload } from "@/lib/contracts.generated";

interface AuditLogsProps {
  audit: AuditPayload;
  /** The active severity filter, owned by the page and sent to the API. */
  severity: string;
  onSeverityChange: (severity: string) => void;
}

/**
 * The severities the AuditLogger actually writes
 * (`agent/security_hardening.py:SecurityEvent`), plus ALL.
 */
const SEVERITIES = ["ALL", "critical", "high", "medium", "low"] as const;

const BADGES: Record<string, { classes: string; icon: React.ReactNode }> = {
  critical: {
    classes: "bg-rose-500/20 text-rose-400 border-rose-500/40",
    icon: <ShieldAlert className="h-3 w-3" />,
  },
  high: {
    classes: "bg-orange-500/20 text-orange-400 border-orange-500/40",
    icon: <AlertTriangle className="h-3 w-3" />,
  },
  medium: {
    classes: "bg-amber-500/20 text-amber-400 border-amber-500/40",
    icon: <AlertTriangle className="h-3 w-3" />,
  },
  low: {
    classes: "bg-slate-700/40 text-slate-300 border-slate-600/40",
    icon: <Info className="h-3 w-3" />,
  },
};

function SeverityBadge({ severity }: { severity: string }) {
  const badge = BADGES[severity.toLowerCase()] ?? BADGES.low;
  return (
    <span
      className={`px-2.5 py-0.5 rounded-full font-mono text-[10px] uppercase font-bold border inline-flex items-center gap-1 ${badge.classes}`}
    >
      {badge.icon}
      {severity}
    </span>
  );
}

function formatDetails(details: AuditEvent["details"]): string {
  const entries = Object.entries(details);
  if (entries.length === 0) return "—";
  return entries.map(([key, value]) => `${key}=${String(value)}`).join(" ");
}

export function AuditLogs({ audit, severity, onSeverityChange }: AuditLogsProps) {
  // Filtering happens server-side now: the page passes `severity` down to the
  // API. Previously this filtered a client-side copy while the API's own
  // severity parameter went unused, so the two could disagree.
  const events = audit.events;

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Shield className="h-5 w-5 text-rose-400" />
            Security Audit Log
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Guardrail and hardening events from <code className="text-slate-300">audit.log</code>
          </p>
        </div>
        <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
          {audit.total.toLocaleString()} shown
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {SEVERITIES.map((sev) => {
          const count = sev === "ALL" ? null : (audit.severity_counts[sev] ?? 0);
          const active = severity === sev;
          return (
            <button
              key={sev}
              onClick={() => onSeverityChange(sev)}
              aria-pressed={active}
              aria-label={`Filter audit log by ${sev} severity`}
              className={`px-3 py-1.5 rounded-xl text-[11px] font-mono border transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
                active
                  ? "bg-cyan-950/50 text-cyan-300 border-cyan-700/50"
                  : "bg-slate-900/60 text-slate-400 border-slate-800 hover:border-slate-700"
              }`}
            >
              {sev}
              {count !== null && <span className="ml-1.5 text-slate-500">{count}</span>}
            </button>
          );
        })}
      </div>

      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-5 py-3">Severity</th>
                <th className="px-5 py-3">Type</th>
                <th className="px-5 py-3">Message</th>
                <th className="px-5 py-3">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {events.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-slate-500 italic">
                    {severity === "ALL"
                      ? "No security audit events recorded."
                      : `No ${severity} severity events recorded.`}
                  </td>
                </tr>
              ) : (
                events.map((event, index) => (
                  <tr
                    key={`${event.timestamp}-${event.type}-${index}`}
                    className="hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="px-5 py-3.5 text-slate-400 whitespace-nowrap text-[11px]">
                      {new Date(event.timestamp * 1000).toISOString().replace("T", " ").slice(0, 19)}
                    </td>
                    <td className="px-5 py-3.5">
                      <SeverityBadge severity={event.severity} />
                    </td>
                    <td className="px-5 py-3.5 font-bold text-slate-200">{event.type || "—"}</td>
                    <td className="px-5 py-3.5 font-sans font-medium text-slate-100">
                      {event.message}
                    </td>
                    <td className="px-5 py-3.5 text-slate-400 text-[11px] font-mono">
                      {formatDetails(event.details)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {audit.total === 0 && severity === "ALL" && (
        <p className="text-xs text-slate-500 flex items-center gap-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
          An empty audit log is a normal state — events are only written when a guardrail acts.
        </p>
      )}
    </div>
  );
}

export default AuditLogs;
