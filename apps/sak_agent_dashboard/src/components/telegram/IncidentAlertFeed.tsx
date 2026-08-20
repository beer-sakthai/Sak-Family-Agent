'use client';

import React from 'react';
import { MobileIncidentAlert } from '../../lib/types';

interface IncidentAlertFeedProps {
  incidents: MobileIncidentAlert[];
  onResolve: (alertId: string, status: 'acknowledged' | 'resolved') => Promise<void>;
}

export const IncidentAlertFeed: React.FC<IncidentAlertFeedProps> = ({
  incidents,
  onResolve,
}) => {
  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'P0_CRITICAL':
        return (
          <span className="rounded bg-rose-950 px-2.5 py-0.5 text-[10px] font-bold text-rose-300 border border-rose-800/60 animate-pulse">
            🚨 P0 CRITICAL
          </span>
        );
      case 'P1_HIGH':
        return (
          <span className="rounded bg-amber-950 px-2.5 py-0.5 text-[10px] font-bold text-amber-300 border border-amber-800/60">
            ⚠️ P1 HIGH
          </span>
        );
      case 'P2_MEDIUM':
        return (
          <span className="rounded bg-blue-950 px-2.5 py-0.5 text-[10px] font-bold text-blue-300 border border-blue-800/60">
            ℹ️ P2 MEDIUM
          </span>
        );
      default:
        return (
          <span className="rounded bg-slate-800 px-2.5 py-0.5 text-[10px] text-slate-300">
            P3 LOW
          </span>
        );
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span>🚨</span> Real-Time Mobile Incident Alert Feed ({incidents.length})
          </h3>
          <p className="text-xs text-slate-400">
            Direct mobile escalations dispatched to Telegram admins with interactive approval gates.
          </p>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {incidents.length === 0 ? (
          <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-6 text-center text-xs text-slate-500">
            No active incidents detected. All agent subsystems operate within safe thresholds.
          </div>
        ) : (
          incidents.map((inc) => (
            <div
              key={inc.alertId}
              className={`rounded-lg border p-4 transition-all ${
                inc.status === 'resolved'
                  ? 'border-slate-800/60 bg-slate-950/40 opacity-60'
                  : 'border-slate-800 bg-slate-950 shadow-sm'
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
                <div className="flex items-center gap-2">
                  {getSeverityBadge(inc.severity)}
                  <span className="font-semibold text-xs text-slate-200">{inc.title}</span>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <span className="rounded bg-slate-800/80 px-2 py-0.5 text-[10px] font-mono text-slate-400">
                    {inc.source}
                  </span>
                  <span
                    className={`rounded px-2 py-0.5 text-[10px] font-semibold ${
                      inc.status === 'resolved'
                        ? 'bg-emerald-950 text-emerald-400'
                        : inc.status === 'acknowledged'
                        ? 'bg-amber-950 text-amber-400'
                        : 'bg-rose-950 text-rose-400'
                    }`}
                  >
                    {inc.status.toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="mt-3 text-xs text-slate-300">
                <p>{inc.details}</p>
                <div className="mt-2 rounded bg-slate-900/80 p-2 font-mono text-[11px] text-amber-300/90">
                  <span className="text-slate-500">Action:</span> {inc.suggestedAction}
                </div>
              </div>

              <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-800/60 pt-2 text-xs">
                <span className="text-[10px] font-mono text-slate-500">
                  ID: {inc.alertId} • {new Date(inc.createdAt).toLocaleTimeString()}
                </span>

                {inc.status !== 'resolved' && (
                  <div className="flex gap-2">
                    {inc.status === 'active' && (
                      <button
                        type="button"
                        onClick={() => onResolve(inc.alertId, 'acknowledged')}
                        className="rounded bg-amber-950 px-2.5 py-1 text-[11px] font-medium text-amber-300 hover:bg-amber-900 border border-amber-800/50"
                      >
                        Acknowledge
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => onResolve(inc.alertId, 'resolved')}
                      className="rounded bg-emerald-950 px-2.5 py-1 text-[11px] font-medium text-emerald-300 hover:bg-emerald-900 border border-emerald-800/50"
                    >
                      ✓ Mark Resolved
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
