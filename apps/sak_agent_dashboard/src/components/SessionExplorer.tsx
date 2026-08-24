"use client";

import React, { useState } from "react";
import { Search, X, Filter, ChevronLeft, ChevronRight, MessageSquare, Terminal, Clock, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import { SessionMeta, SessionTranscript } from "@/lib/types";

interface SessionExplorerProps {
  sessions: SessionMeta[];
  total?: number;
  onSearchChange?: (query: string) => void;
  onSessionSelect?: (sessionId: string) => void;
  selectedSessionDetail?: SessionTranscript | null;
  isLoadingDetail?: boolean;
}

export function SessionExplorer({
  sessions,
  total,
  onSearchChange,
  onSessionSelect,
  selectedSessionDetail,
  isLoadingDetail = false,
}: SessionExplorerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [personaFilter, setPersonaFilter] = useState("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // Local active session modal state if parent didn't supply selectedSessionDetail
  const [activeModalSession, setActiveModalSession] = useState<SessionTranscript | SessionMeta | null>(null);

  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchQuery(val);
    if (onSearchChange) {
      onSearchChange(val);
    }
  };

  // Filter sessions client-side
  const filteredSessions = sessions.filter((s) => {
    const matchesSearch =
      !searchQuery ||
      s.sessionId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.persona.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || s.status === statusFilter;
    const matchesPersona = personaFilter === "ALL" || s.persona === personaFilter;

    return matchesSearch && matchesStatus && matchesPersona;
  });

  const totalPages = Math.max(1, Math.ceil(filteredSessions.length / itemsPerPage));
  const paginatedSessions = filteredSessions.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handleOpenDetail = (session: SessionMeta) => {
    if (onSessionSelect) {
      onSessionSelect(session.sessionId);
    }
    setActiveModalSession(session);
  };

  const activeDetail = selectedSessionDetail || (activeModalSession as SessionTranscript);

  return (
    <div className="space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight">
            Session History & Transcript Explorer
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Search session transcripts, inspect prompt history, token usage, and raw JSON execution metadata
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 px-3 py-1 rounded-full w-fit">
          <Terminal className="h-3.5 w-3.5" />
          Showing {filteredSessions.length} of {total ?? sessions.length} Sessions
        </div>
      </div>

      {/* Filter Bar */}
      <div className="glass-panel p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl flex flex-col md:flex-row gap-3 justify-between items-center">
        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search sessions or personas..."
            value={searchQuery}
            onChange={handleSearchInputChange}
            className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 font-mono transition-all"
          />
          {searchQuery && (
            <button
              type="button"
              aria-label="Clear search query"
              onClick={() => {
                setSearchQuery("");
                if (onSearchChange) onSearchChange("");
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 rounded"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Dropdown Filters */}
        <div className="flex items-center gap-3 w-full md:w-auto font-mono text-xs">
          <div className="flex items-center gap-1.5 text-slate-400">
            <Filter className="h-3.5 w-3.5 text-cyan-400" />
            <span>Filter:</span>
          </div>

          <select
            aria-label="Filter sessions by persona"
            value={personaFilter}
            onChange={(e) => {
              setPersonaFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus:border-cyan-500"
          >
            <option value="ALL">All Personas</option>
            <option value="SakThai">SakThai</option>
            <option value="SakKing">SakKing</option>
            <option value="SakSee">SakSee</option>
            <option value="SakSit">SakSit</option>
            <option value="SakJules">SakJules</option>
          </select>

          <select
            aria-label="Filter sessions by status"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus:border-cyan-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Session Table */}
      <div className="glass-panel rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800/80 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3">Session ID</th>
                <th className="px-5 py-3">Persona</th>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-5 py-3">Messages</th>
                <th className="px-5 py-3">Tokens</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {paginatedSessions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center text-slate-500 italic">
                    No sessions match the current search or filter criteria.
                  </td>
                </tr>
              ) : (
                paginatedSessions.map((session) => (
                  <tr
                    key={session.sessionId}
                    className="hover:bg-slate-800/50 transition-colors duration-150 group"
                  >
                    <td className="px-5 py-3.5 font-bold text-cyan-300">
                      {session.sessionId}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700">
                        {session.persona}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-slate-400">
                      {session.timestamp}
                    </td>
                    <td className="px-5 py-3.5 text-slate-300">
                      {session.messageCount} msgs
                    </td>
                    <td className="px-5 py-3.5 text-emerald-400 font-bold">
                      {session.tokenUsage.toLocaleString()}
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] uppercase font-bold border ${
                          session.status === "completed"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                            : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                        }`}
                      >
                        {session.status === "completed" ? (
                          <CheckCircle2 className="h-3 w-3" />
                        ) : (
                          <AlertCircle className="h-3 w-3" />
                        )}
                        {session.status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        type="button"
                        aria-label={`Inspect session ${session.sessionId} details`}
                        onClick={() => handleOpenDetail(session)}
                        className="px-3 py-1 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 hover:bg-cyan-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 transition-all font-sans font-semibold text-xs inline-flex items-center gap-1"
                      >
                        <FileText className="h-3.5 w-3.5" />
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/60 flex items-center justify-between font-mono text-xs">
          <span className="text-slate-400">
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              aria-label="Previous page"
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="p-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              type="button"
              aria-label="Next page"
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              className="p-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Interactive Modal Detail Viewer */}
      {activeModalSession && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 font-mono text-xs text-cyan-400">
                  <Terminal className="h-4 w-4" />
                  Session Transcript Detail
                </div>
                <h4 className="text-lg font-bold font-display text-white mt-0.5">
                  {activeModalSession.sessionId}
                </h4>
              </div>
              <button
                type="button"
                aria-label="Close session detail modal"
                onClick={() => setActiveModalSession(null)}
                className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 font-mono text-xs">
              {/* Metadata Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                  <span className="text-slate-500 uppercase text-[10px]">Persona</span>
                  <div className="font-bold text-cyan-300">{activeModalSession.persona}</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                  <span className="text-slate-500 uppercase text-[10px]">Tokens Used</span>
                  <div className="font-bold text-emerald-300">{activeModalSession.tokenUsage.toLocaleString()}</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                  <span className="text-slate-500 uppercase text-[10px]">Status</span>
                  <div className="font-bold text-white">{activeModalSession.status}</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                  <span className="text-slate-500 uppercase text-[10px]">Timestamp</span>
                  <div className="font-bold text-slate-300">{activeModalSession.timestamp}</div>
                </div>
              </div>

              {/* Task description if available */}
              {activeDetail?.task && (
                <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-800/40">
                  <span className="text-[10px] uppercase font-bold text-cyan-400 block mb-1">
                    Task / Objective
                  </span>
                  <p className="text-slate-200 font-sans">{activeDetail.task}</p>
                </div>
              )}

              {/* Conversation Messages */}
              <div className="space-y-3">
                <h5 className="font-bold text-sm text-slate-200 font-display flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-cyan-400" />
                  Transcript Messages
                </h5>

                {activeDetail?.messages && activeDetail.messages.length > 0 ? (
                  <div className="space-y-3">
                    {activeDetail.messages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`p-4 rounded-xl border font-sans text-xs ${
                          msg.role === "user"
                            ? "bg-slate-950/80 border-slate-800 text-slate-200"
                            : "bg-cyan-950/30 border-cyan-800/40 text-cyan-100"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2 font-mono text-[10px] text-slate-400">
                          <span className="font-bold uppercase tracking-wider text-cyan-400">
                            {msg.role} {msg.name ? `(${msg.name})` : ""}
                          </span>
                          {msg.timestamp && <span>{msg.timestamp}</span>}
                        </div>
                        <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-slate-400 italic">
                    Sample conversation log: User prompt initiated task execution. Persona {activeModalSession.persona} processed instructions successfully with 0 policy flags.
                  </div>
                )}
              </div>

              {/* Raw Execution Result / Metadata */}
              <div className="space-y-2">
                <h5 className="font-bold text-sm text-slate-200 font-display">
                  Execution Result & Raw Metadata
                </h5>
                <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 font-mono text-xs overflow-x-auto">
                  {JSON.stringify(
                    activeDetail?.result || {
                      sessionId: activeModalSession.sessionId,
                      persona: activeModalSession.persona,
                      status: activeModalSession.status,
                      tokenUsage: activeModalSession.tokenUsage,
                      stop_reason: "end_turn",
                    },
                    null,
                    2
                  )}
                </pre>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/80 flex justify-end">
              <button
                onClick={() => setActiveModalSession(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 font-sans font-semibold text-xs transition-colors"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SessionExplorer;
