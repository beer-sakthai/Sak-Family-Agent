"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  FileText,
  MessageSquare,
  Search,
  Terminal,
  X,
} from "lucide-react";

import { UNATTRIBUTED, type SessionDetail, type SessionSummary } from "@/lib/contracts.generated";

interface SessionExplorerProps {
  sessions: SessionSummary[];
  total: number;
  /** Search is server-side; the page owns the query and refetches. */
  search: string;
  onSearchChange: (query: string) => void;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onSessionSelect: (sessionId: string | null) => void;
  detail: SessionDetail | null;
  isLoadingDetail?: boolean;
}

function formatTimestamp(epochSeconds: number): string {
  if (!epochSeconds) return "—";
  return new Date(epochSeconds * 1000).toISOString().replace("T", " ").slice(0, 19);
}

/** A session with no persona is shown as such, never assigned to one. */
function personaLabel(persona: string | null): string {
  return persona ?? UNATTRIBUTED;
}

export function SessionExplorer({
  sessions,
  total,
  search,
  onSearchChange,
  page,
  pageSize,
  onPageChange,
  onSessionSelect,
  detail,
  isLoadingDetail = false,
}: SessionExplorerProps) {
  const [openSessionId, setOpenSessionId] = useState<string | null>(null);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const openDetail = (session: SessionSummary) => {
    setOpenSessionId(session.id);
    onSessionSelect(session.id);
  };

  const closeDetail = () => {
    setOpenSessionId(null);
    onSessionSelect(null);
  };

  const openSummary = sessions.find((s) => s.id === openSessionId) ?? detail?.summary ?? null;

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-fg tracking-tight flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-hue-cyan" />
            Session Explorer
          </h3>
          <p className="text-xs text-fg-3 mt-0.5">
            Agent transcripts from <code className="text-fg-2">~/.sakthai/sessions/</code>
          </p>
        </div>
        <span className="text-xs font-mono px-3 py-1 rounded-full bg-panel border border-line text-hue-cyan">
          {total.toLocaleString()} {total === 1 ? "session" : "sessions"}
        </span>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-fg-4 pointer-events-none" />
        <input
          type="text"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search sessions by task, model, id, or persona…"
          aria-label="Search sessions"
          className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-panel/80 border border-line text-sm text-fg placeholder:text-fg-5 font-mono focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus:border-hue-cyan-line/50 transition-colors"
        />
        {search && (
          <button
            type="button"
            aria-label="Clear search query"
            title="Clear search query"
            onClick={() => onSearchChange("")}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 rounded-md text-fg-3 hover:text-fg hover:bg-raised/80 active:bg-raised-2/80 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      <div className="glass-panel rounded-2xl bg-panel/80 border border-line/80 backdrop-blur-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-sunken/80 text-fg-3 border-b border-line/80 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3">Persona</th>
                <th className="px-5 py-3">Task</th>
                <th className="px-5 py-3">Model</th>
                <th className="px-5 py-3">When</th>
                <th className="px-5 py-3 text-right">Tokens</th>
                <th className="px-5 py-3">Outcome</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-line/60 text-fg-2">
              {sessions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center">
                    <div className="flex flex-col items-center justify-center gap-2 font-sans">
                      <p className="text-fg-4 text-xs">
                        {search
                          ? `No sessions match \u201C${search}\u201D.`
                          : "No sessions recorded yet."}
                      </p>
                      {search && (
                        <button
                          type="button"
                          aria-label="Clear search and filters"
                          onClick={() => onSearchChange("")}
                          className="px-3 py-1 rounded-lg bg-raised text-hue-cyan hover:text-hue-cyan hover:bg-raised-2 font-mono text-xs border border-line-strong transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                        >
                          Reset search
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                sessions.map((session) => (
                  <tr key={session.id} className="hover:bg-raised/40 transition-colors">
                    <td className="px-5 py-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] border ${
                          session.persona
                            ? "bg-raised text-hue-cyan border-hue-cyan-line/20"
                            : "bg-panel text-fg-4 border-line-strong"
                        }`}
                      >
                        {personaLabel(session.persona)}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 font-sans text-fg max-w-md truncate">
                      {session.task || "—"}
                    </td>
                    <td className="px-5 py-3.5 text-fg-3 text-[11px] max-w-[12rem] truncate">
                      {session.model || "—"}
                    </td>
                    <td className="px-5 py-3.5 text-fg-4 text-[11px] whitespace-nowrap">
                      {formatTimestamp(session.timestamp)}
                    </td>
                    <td className="px-5 py-3.5 text-right text-fg-2">
                      {session.tokens.total_tokens.toLocaleString()}
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center gap-1 text-[11px] ${
                          session.had_error ? "text-hue-rose" : "text-hue-emerald"
                        }`}
                      >
                        {session.had_error ? (
                          <AlertCircle className="h-3 w-3" />
                        ) : (
                          <CheckCircle2 className="h-3 w-3" />
                        )}
                        {session.stop_reason || "—"}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => openDetail(session)}
                        className="text-[11px] px-2.5 py-1 rounded-lg bg-raised border border-line-strong text-hue-cyan hover:border-hue-cyan-line/60 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs font-mono text-fg-3">
          <span>
            Page {page} of {totalPages}
          </span>
          <div className="flex items-center gap-2">
            {/* A disabled icon button explains nothing about why it is
                disabled; the title says which end of the list you are at.
                Ported from PR #1180, which was written against the local-state
                version of this component that the server-driven rewrite
                replaced. */}
            <button
              onClick={() => onPageChange(Math.max(1, page - 1))}
              disabled={page <= 1}
              aria-label="Previous page"
              title={page <= 1 ? "First page reached" : "Previous page"}
              className="px-3 py-1.5 rounded-lg bg-panel border border-line disabled:opacity-40 hover:border-line-strong transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => onPageChange(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              aria-label="Next page"
              title={page >= totalPages ? "Last page reached" : "Next page"}
              className="px-3 py-1.5 rounded-lg bg-panel border border-line disabled:opacity-40 hover:border-line-strong transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}

      {openSessionId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-sunken/80 backdrop-blur-sm p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Session transcript"
          onClick={closeDetail}
        >
          <div
            className="w-full max-w-3xl max-h-[85vh] overflow-y-auto rounded-2xl bg-panel border border-line shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 flex items-center justify-between px-6 py-4 bg-panel border-b border-line">
              <h4 className="font-display font-bold text-fg flex items-center gap-2">
                <Terminal className="h-4 w-4 text-hue-cyan" />
                Session transcript
              </h4>
              <button
                onClick={closeDetail}
                aria-label="Close transcript"
                className="p-1.5 rounded-lg hover:bg-raised text-fg-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="p-6 space-y-5 font-mono text-xs">
              {openSummary && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div>
                    <span className="text-[10px] uppercase text-fg-4 block">Persona</span>
                    <span className="font-bold text-hue-cyan">
                      {personaLabel(openSummary.persona)}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-fg-4 block">Model</span>
                    <span className="font-bold text-fg truncate block">
                      {openSummary.model || "—"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-fg-4 block">Iterations</span>
                    <span className="font-bold text-fg">{openSummary.iterations}</span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-fg-4 flex items-center gap-1">
                      <Clock className="h-3 w-3" /> When
                    </span>
                    <span className="font-bold text-fg-2">
                      {formatTimestamp(openSummary.timestamp)}
                    </span>
                  </div>
                </div>
              )}

              {openSummary?.task && (
                <div className="p-3 rounded-xl bg-sunken/60 border border-line">
                  <span className="text-[10px] uppercase text-fg-4 flex items-center gap-1 mb-1">
                    <FileText className="h-3 w-3" /> Task
                  </span>
                  <p className="text-fg font-sans">{openSummary.task}</p>
                </div>
              )}

              {isLoadingDetail ? (
                <p className="text-fg-4 italic">Loading transcript…</p>
              ) : detail && detail.messages.length > 0 ? (
                <div className="space-y-2">
                  <span className="text-[10px] uppercase text-fg-4">
                    Messages ({detail.messages.length})
                  </span>
                  {detail.messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-sunken/60 border border-line space-y-1"
                    >
                      <span
                        className={`text-[10px] uppercase font-bold ${
                          msg.role === "user" ? "text-hue-cyan" : "text-hue-emerald"
                        }`}
                      >
                        {msg.role}
                      </span>
                      <p className="text-fg font-sans whitespace-pre-wrap break-words">
                        {msg.content}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-fg-4 italic">
                  This session recorded no message transcript.
                </p>
              )}

              {detail && detail.tool_calls.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[10px] uppercase text-fg-4">
                    Tool calls ({detail.tool_calls.length})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {detail.tool_calls.map((call, idx) => (
                      <span
                        key={`${call.name}-${idx}`}
                        className={`px-2 py-0.5 rounded-full text-[10px] border ${
                          call.is_error
                            ? "bg-hue-rose-tint/40 text-hue-rose border-hue-rose-line/40"
                            : "bg-hue-cyan-tint/40 text-hue-cyan border-hue-cyan-line/30"
                        }`}
                      >
                        {call.name}
                        {call.is_error && " ✕"}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {detail?.result_text && (
                <div className="p-3 rounded-xl bg-sunken/60 border border-line">
                  <span className="text-[10px] uppercase text-fg-4 block mb-1">Result</span>
                  <p className="text-fg font-sans whitespace-pre-wrap break-words">
                    {detail.result_text}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SessionExplorer;
