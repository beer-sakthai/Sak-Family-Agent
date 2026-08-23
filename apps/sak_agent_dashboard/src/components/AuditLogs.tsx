"use client";

import React, { useState } from "react";
import { Shield, ShieldAlert, Filter, AlertTriangle, Info } from "lucide-react";
import { AuditLog, AuditSeverity } from "@/lib/types";

interface AuditLogsProps {
  logs: AuditLog[];
  onSeverityChange?: (severity: string) => void;
}

export function AuditLogs({ logs, onSeverityChange }: AuditLogsProps) {
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");

  const handleSeveritySelect = (sev: string) => {
    setSelectedSeverity(sev);
    if (onSeverityChange) {
      onSeverityChange(sev);
    }
  };

  const filteredLogs = logs.filter((log) => {
    if (selectedSeverity === "ALL") return true;
    return log.severity.toLowerCase() === selectedSeverity.toLowerCase();
  });

  const getSeverityBadge = (severity: AuditSeverity | string) => {
    const sev = severity.toLowerCase();
    if (sev === "critical") {
      return (
        <span className="px-2.5 py-0.5 rounded-full font-mono text-[10px] uppercase font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 flex items-center gap-1">
          <ShieldAlert className="h-3 w-3" />
          critical
        </span>
      );
    }
    if (sev === "warning" || sev === "warn") {
      return (
        <span className="px-2.5 py-0.5 rounded-full font-mono text-[10px] uppercase font-bold bg-amber-500/20 text-amber-400 border border-amber-500/40 flex items-center gap-1">
          <AlertTriangle className="h-3 w-3" />
          warning
        </span>
      );
    }
    if (sev === "error") {
      return (
        <span className="px-2.5 py-0.5 rounded-full font-mono text-[10px] uppercase font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1">
          <ShieldAlert className="h-3 w-3" />
          error
        </span>
      );
    }
    return (
      <span className="px-2.5 py-0.5 rounded-full font-mono text-[10px] uppercase font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 flex items-center gap-1">
        <Info className="h-3 w-3" />
        info
      </span>
    );
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight flex items-center gap-2">
            <Shield className="h-5 w-5 text-rose-400" />
            Security Audit Log Inspector (`audit.log`)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time security event log inspector tracking persona actions, boundary validations, and security events
          </p>
        </div>

        {/* Severity Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-950/80 border border-slate-800/80 font-mono text-xs w-fit">
          <span className="text-slate-500 px-2 text-[10px] uppercase flex items-center gap-1">
            <Filter className="h-3 w-3 text-cyan-400" /> Severity:
          </span>
          {["ALL", "INFO", "WARNING", "CRITICAL"].map((sev) => (
            <button
              key={sev}
              onClick={() => handleSeveritySelect(sev)}
              className={`px-3 py-1 rounded-lg text-[11px] uppercase font-bold transition-all ${
                selectedSeverity === sev
                  ? "bg-slate-800 text-cyan-400 border border-cyan-500/30 shadow"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-5 py-3">Severity</th>
                <th className="px-5 py-3">Persona</th>
                <th className="px-5 py-3">Event Summary</th>
                <th className="px-5 py-3">Details / Context</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-slate-500 italic">
                    No security audit events recorded matching severity level "{selectedSeverity}".
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-3.5 text-slate-400 whitespace-nowrap text-[11px]">
                      {log.timestamp}
                    </td>
                    <td className="px-5 py-3.5">
                      {getSeverityBadge(log.severity)}
                    </td>
                    <td className="px-5 py-3.5 font-bold text-slate-200">
                      {log.persona}
                    </td>
                    <td className="px-5 py-3.5 font-sans font-medium text-slate-100">
                      {log.event}
                    </td>
                    <td className="px-5 py-3.5 text-slate-400 text-[11px] font-mono">
                      {log.details}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default AuditLogs;
