"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  BookOpen,
  Database,
  Layers,
  Lightbulb,
  Plus,
  Trash2,
  Search,
  Sparkles,
  ShieldAlert,
  CheckCircle2,
  X,
  RefreshCw,
  Eye,
  Tag,
} from "lucide-react";

import type { MemoryPayload } from "@/lib/contracts.generated";

interface MemoryExplorerProps {
  memory: MemoryPayload;
}

interface FactItem {
  id: number;
  persona: string;
  kind: string;
  key?: string | null;
  value: string;
  tags?: string[];
  updated_at: number;
  created_at?: number;
}

interface ShardMeta {
  persona: string;
  name: string;
  role: string;
  size_bytes: number;
  facts_count: number;
  observations_count: number;
}

const SHARD_TABS = [
  { id: "all", label: "All Shards (Merged)", color: "text-hue-emerald" },
  { id: "sakthai", label: "SakThai", color: "text-amber-400" },
  { id: "sakking", label: "SakKing", color: "text-blue-400" },
  { id: "saksee", label: "SakSee", color: "text-cyan-400" },
  { id: "sakjules", label: "SakJules", color: "text-violet-400" },
  { id: "saksit", label: "SakSit", color: "text-pink-400" },
  { id: "saktan", label: "SakTan", color: "text-emerald-400" },
];

const KIND_FILTERS = ["all", "fact", "pref", "goal", "pattern", "note"] as const;

function timestamp(epochSeconds: number): string {
  if (!epochSeconds) return "—";
  return new Date(epochSeconds * 1000).toISOString().replace("T", " ").slice(0, 16);
}

export function MemoryExplorer({ memory }: MemoryExplorerProps) {
  const [selectedShard, setSelectedShard] = useState<string>("all");
  const [activeTab, setActiveTab] = useState<"facts" | "observations" | "simulator">("facts");
  const [selectedKind, setSelectedKind] = useState<string>("all");
  const [searchFilter, setSearchFilter] = useState<string>("");

  // Live state fetched from Gateway
  const [shards, setShards] = useState<ShardMeta[]>([]);
  const [dynamicFacts, setDynamicFacts] = useState<FactItem[]>([]);

  // Modal states
  const [addModalOpen, setAddModalOpen] = useState<boolean>(false);
  const [addPersona, setAddPersona] = useState<string>("sakthai");
  const [addKind, setAddKind] = useState<string>("fact");
  const [addKey, setAddKey] = useState<string>("");
  const [addValue, setAddValue] = useState<string>("");
  const [addTags, setAddTags] = useState<string>("");
  const [approvalToken, setApprovalToken] = useState<string>("");
  const [guardrailBlockReason, setGuardrailBlockReason] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);

  // Delete modal states
  const [deleteModalOpen, setDeleteModalOpen] = useState<boolean>(false);
  const [factToDelete, setFactToDelete] = useState<FactItem | null>(null);
  const [deleteConfirmed, setDeleteConfirmed] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  // Simulator states
  const [simQuery, setSimQuery] = useState<string>("Review PR verification and CI guardrails");
  const [simPersona, setSimPersona] = useState<string>("sakjules");
  const [simResult, setSimResult] = useState<{
    prompt_context: string;
    facts: FactItem[];
    observations: { summary: string }[];
  } | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  // Fetch shards metadata on mount
  useEffect(() => {
    fetchShards();
  }, []);

  const fetchShards = async () => {
    try {
      const res = await fetch("/api/gateway/memory/shards");
      if (res.ok) {
        const data = await res.json();
        if (data.ok && Array.isArray(data.shards)) {
          setShards(data.shards);
        }
      }
    } catch {
      // Fallback gracefully
    }
  };

  // Fetch persona facts when shard changes
  const fetchFactsForShard = async (shardId: string) => {
    if (shardId === "all") {
      setDynamicFacts([]);
      return;
    }
    try {
      const res = await fetch(`/api/gateway/memory?persona=${shardId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.ok && Array.isArray(data.facts)) {
          setDynamicFacts(
            data.facts.map((f: Record<string, unknown>, idx: number) => ({
              id: (f.id as number) ?? idx + 1,
              persona: shardId,
              kind: (f.kind as string) ?? "fact",
              key: (f.key as string) ?? "",
              value: (f.value as string) ?? "",
              tags: Array.isArray(f.tags) ? f.tags : [],
              updated_at: (f.updated_at as number) ?? Math.floor(Date.now() / 1000),
            }))
          );
        }
      }
    } catch {
      // Fallback
    }
  };

  const handleShardChange = (shardId: string) => {
    setSelectedShard(shardId);
    fetchFactsForShard(shardId);
  };

  // Facts to display: either dynamic shard facts or initial merged memory facts
  const baseFacts: FactItem[] = useMemo(() => {
    if (selectedShard !== "all") {
      if (dynamicFacts.length > 0) {
        return dynamicFacts;
      }
      return memory.facts
        .filter((f) => f.persona === selectedShard)
        .map((f, idx) => ({
          id: f.id ?? idx + 1,
          persona: f.persona,
          kind: f.kind,
          key: f.key,
          value: f.value,
          tags: f.tags || [],
          updated_at: f.updated_at,
        }));
    }
    return memory.facts.map((f, idx) => ({
      id: f.id ?? idx + 1,
      persona: f.persona || "sakthai",
      kind: f.kind,
      key: f.key,
      value: f.value,
      tags: f.tags || [],
      updated_at: f.updated_at,
    }));
  }, [selectedShard, dynamicFacts, memory.facts]);

  // Filtered facts
  const filteredFacts = useMemo(() => {
    return baseFacts.filter((f) => {
      if (selectedKind !== "all" && f.kind.toLowerCase() !== selectedKind.toLowerCase()) {
        return false;
      }
      if (searchFilter.trim()) {
        const q = searchFilter.toLowerCase();
        const inVal = f.value.toLowerCase().includes(q);
        const inKey = (f.key || "").toLowerCase().includes(q);
        const inTags = (f.tags || []).some((t) => t.toLowerCase().includes(q));
        return inVal || inKey || inTags;
      }
      return true;
    });
  }, [baseFacts, selectedKind, searchFilter]);

  // Handle Add Fact Submit
  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addValue.trim()) return;

    setIsSubmitting(true);
    setGuardrailBlockReason(null);
    setSubmitSuccess(null);

    const tagsArray = addTags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    try {
      const res = await fetch("/api/gateway/memory/mutate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          persona: addPersona,
          kind: addKind,
          key: addKey.trim() || undefined,
          value: addValue.trim(),
          tags: tagsArray,
          approval_token: approvalToken.trim() || undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok || !data.ok) {
        if (data.status === "blocked") {
          setGuardrailBlockReason(data.error || "Blocked by DataLossGuardrail");
          if (data.approval_token) {
            setApprovalToken(data.approval_token);
          }
        } else {
          setGuardrailBlockReason(data.error || "Failed to create fact");
        }
      } else {
        setSubmitSuccess(`Fact saved successfully to ${addPersona} shard.`);
        setAddValue("");
        setAddKey("");
        setAddTags("");
        setApprovalToken("");
        fetchShards();
        fetchFactsForShard(selectedShard);
        setTimeout(() => {
          setAddModalOpen(false);
          setSubmitSuccess(null);
        }, 1200);
      }
    } catch (err: unknown) {
      setGuardrailBlockReason(err instanceof Error ? err.message : String(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Delete Fact Submit
  const handleDeleteSubmit = async () => {
    if (!factToDelete || !deleteConfirmed) return;

    setIsDeleting(true);
    const targetPersona = factToDelete.persona || selectedShard || "sakthai";

    try {
      const res = await fetch(
        `/api/gateway/memory/mutate?id=${factToDelete.id}&persona=${targetPersona}&confirmed=true`,
        { method: "DELETE" }
      );
      if (res.ok) {
        setDeleteModalOpen(false);
        setFactToDelete(null);
        setDeleteConfirmed(false);
        fetchShards();
        fetchFactsForShard(selectedShard);
      }
    } catch {
      // Handle error
    } finally {
      setIsDeleting(false);
    }
  };

  // Handle Run Simulator Preview
  const handleRunSimulator = async () => {
    if (!simQuery.trim()) return;

    setIsSimulating(true);
    setSimResult(null);

    try {
      const res = await fetch("/api/gateway/memory/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          persona: simPersona,
          query: simQuery.trim(),
          limit: 5,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.ok) {
          setSimResult({
            prompt_context: data.prompt_context || "No memory context generated.",
            facts: data.facts || [],
            observations: data.observations || [],
          });
        }
      }
    } catch {
      // Handle error
    } finally {
      setIsSimulating(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowRight") {
      e.preventDefault();
      const nextTab =
        activeTab === "facts"
          ? "observations"
          : activeTab === "observations"
          ? "simulator"
          : "facts";
      setActiveTab(nextTab);
      document.getElementById(`tab-${nextTab}`)?.focus();
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      const prevTab =
        activeTab === "facts"
          ? "simulator"
          : activeTab === "observations"
          ? "facts"
          : "observations";
      setActiveTab(prevTab);
      document.getElementById(`tab-${prevTab}`)?.focus();
    } else if (e.key === "Home") {
      e.preventDefault();
      setActiveTab("facts");
      document.getElementById("tab-facts")?.focus();
    } else if (e.key === "End") {
      e.preventDefault();
      setActiveTab("observations");
      document.getElementById("tab-observations")?.focus();
    }
  };

  return (
    <div className="space-y-4">
      {/* Header with Title and Global Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold font-display text-fg tracking-tight flex items-center gap-2">
            <Database className="h-5 w-5 text-hue-emerald" aria-hidden="true" />
            Memory Shard Studio &amp; Explorer
          </h3>
          <p className="text-xs text-fg-3 mt-0.5">
            Per-persona SQLite shards, semantic kind filtering, safe mutations, and dynamic prompt injection preview
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs flex-wrap">
          <span
            role="status"
            aria-label={`Total recorded facts across shards: ${memory.total_facts.toLocaleString()}${memory.facts_this_week > 0 ? ` (${memory.facts_this_week} added this week)` : ""}`}
            className="px-3 py-1 rounded-full bg-panel border border-line text-hue-cyan"
            title={`Total recorded facts across shards: ${memory.total_facts.toLocaleString()}${memory.facts_this_week > 0 ? ` (${memory.facts_this_week} added this week)` : ""}`}
          >
            {memory.total_facts.toLocaleString()} facts
            {memory.facts_this_week > 0 && (
              <span className="text-hue-emerald"> (+{memory.facts_this_week} this week)</span>
            )}
          </span>
          <span
            role="status"
            aria-label={`Total recorded observations across shards: ${memory.total_observations.toLocaleString()}`}
            className="px-3 py-1 rounded-full bg-panel border border-line text-hue-violet"
            title={`Total recorded observations across shards: ${memory.total_observations.toLocaleString()}`}
          >
            {memory.total_observations.toLocaleString()} observations
          </span>
          <button
            type="button"
            onClick={() => setAddModalOpen(true)}
            className="px-3 py-1.5 rounded-xl bg-hue-emerald-tint/70 text-hue-emerald border border-hue-emerald-line text-xs font-mono font-semibold flex items-center gap-1.5 hover:bg-hue-emerald-tint hover:border-hue-emerald transition-colors cursor-pointer shadow-xs"
          >
            <Plus className="h-3.5 w-3.5" />
            Add Fact
          </button>
          <button
            type="button"
            onClick={() => {
              fetchShards();
              fetchFactsForShard(selectedShard);
            }}
            title="Refresh memory shards"
            className="p-1.5 rounded-xl bg-panel border border-line text-fg-3 hover:text-fg hover:border-line-strong transition-colors cursor-pointer"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Shard Selector Tab Bar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-line pb-3">
        {SHARD_TABS.map((tab) => {
          const isSelected = selectedShard === tab.id;
          const shardInfo = shards.find((s) => s.persona === tab.id);

          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => handleShardChange(tab.id)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-mono border transition-all flex items-center gap-2 cursor-pointer ${
                isSelected
                  ? "bg-hue-emerald-tint/50 text-hue-emerald border-hue-emerald-line shadow-xs font-bold"
                  : "bg-panel/50 text-fg-3 border-line hover:border-line-strong hover:text-fg"
              }`}
            >
              <Database className={`h-3 w-3 ${tab.color}`} />
              <span>{tab.label}</span>
              {shardInfo && (
                <span className="text-[10px] opacity-75 bg-canvas px-1.5 py-0.2 rounded border border-line">
                  {shardInfo.facts_count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* View Sub-Tabs Bar & Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
        <div
          role="tablist"
          aria-label="Memory Explorer tabs"
          onKeyDown={handleKeyDown}
          className="flex items-center gap-2"
        >
          <button
            id="tab-facts"
            type="button"
            role="tab"
            tabIndex={activeTab === "facts" ? 0 : -1}
            aria-selected={activeTab === "facts"}
            aria-controls="panel-facts"
            title={activeTab === "facts" ? "Viewing recorded memory facts" : "Switch to memory facts view"}
            onClick={() => setActiveTab("facts")}
            className={`px-4 py-2 rounded-xl text-xs font-mono border transition-colors cursor-pointer focus:outline-hidden focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-canvas ${
              activeTab === "facts"
                ? "bg-hue-cyan-tint/50 text-hue-cyan border-hue-cyan-line/50 font-bold"
                : "bg-panel/60 text-fg-3 border-line hover:border-line-strong"
            }`}
          >
            <BookOpen className="h-3.5 w-3.5 inline mr-1.5" aria-hidden="true" />
            Facts ({filteredFacts.length})
          </button>
          <button
            id="tab-observations"
            type="button"
            role="tab"
            tabIndex={activeTab === "observations" ? 0 : -1}
            aria-selected={activeTab === "observations"}
            aria-controls="panel-observations"
            title={activeTab === "observations" ? "Viewing recorded observations" : "Switch to observations view"}
            onClick={() => setActiveTab("observations")}
            className={`px-4 py-2 rounded-xl text-xs font-mono border transition-colors cursor-pointer focus:outline-hidden focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-canvas ${
              activeTab === "observations"
                ? "bg-hue-violet-tint/50 text-hue-violet border-hue-violet-line/50 font-bold"
                : "bg-panel/60 text-fg-3 border-line hover:border-line-strong"
            }`}
          >
            <Lightbulb className="h-3.5 w-3.5 inline mr-1.5" aria-hidden="true" />
            Observations ({memory.observations.length})
          </button>
          <button
            id="tab-simulator"
            type="button"
            role="tab"
            tabIndex={activeTab === "simulator" ? 0 : -1}
            aria-selected={activeTab === "simulator"}
            aria-controls="panel-simulator"
            title={activeTab === "simulator" ? "Viewing prompt injection preview" : "Switch to prompt injection preview"}
            onClick={() => setActiveTab("simulator")}
            className={`px-4 py-2 rounded-xl text-xs font-mono border transition-colors cursor-pointer focus:outline-hidden focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-canvas ${
              activeTab === "simulator"
                ? "bg-hue-emerald-tint/50 text-hue-emerald border-hue-emerald-line font-bold"
                : "bg-panel/60 text-fg-3 border-line hover:border-line-strong"
            }`}
          >
            <Eye className="h-3.5 w-3.5 inline mr-1.5" aria-hidden="true" />
            Prompt Simulator
          </button>
        </div>

        {/* Search & Filter Bar (Only in Facts Tab) */}
        {activeTab === "facts" && (
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1 bg-panel border border-line rounded-lg px-2.5 py-1">
              <Search className="h-3.5 w-3.5 text-fg-3" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Filter facts or tags..."
                className="bg-transparent text-xs font-mono text-fg placeholder:text-fg-3 focus:outline-hidden w-36 sm:w-44"
              />
              {searchFilter && (
                <button
                  type="button"
                  onClick={() => setSearchFilter("")}
                  className="text-fg-3 hover:text-fg cursor-pointer"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>

            {/* Kind Filter Chips */}
            <div className="flex items-center gap-1">
              {KIND_FILTERS.map((kind) => {
                const active = selectedKind === kind;
                return (
                  <button
                    key={kind}
                    type="button"
                    onClick={() => setSelectedKind(kind)}
                    className={`px-2 py-0.5 rounded text-[11px] font-mono border transition-colors cursor-pointer uppercase ${
                      active
                        ? "bg-fg text-canvas font-bold border-fg"
                        : "bg-canvas text-fg-3 border-line hover:border-line-strong hover:text-fg"
                    }`}
                  >
                    {kind}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Main Tab Panels */}
      {activeTab === "facts" && (
        <div
          role="tabpanel"
          id="panel-facts"
          aria-labelledby="tab-facts"
          tabIndex={0}
          className="glass-panel rounded-2xl bg-panel/80 border border-line/80 backdrop-blur-xl overflow-hidden shadow-xl focus:outline-hidden focus-visible:ring-2 focus-visible:ring-accent"
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-sunken/80 text-fg-3 border-b border-line/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th title="Unique memory fact identifier" className="px-5 py-3">ID</th>
                  <th title="Memory category kind and lookup key" className="px-5 py-3">Kind / Key</th>
                  <th title="Stored fact content and associated tags" className="px-5 py-3">Value</th>
                  <th title="Source persona database shard" className="px-5 py-3">Shard</th>
                  <th title="Last updated timestamp (UTC)" className="px-5 py-3 text-right">Updated</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/60 text-fg-2">
                {filteredFacts.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-5 py-8 text-center">
                      <div className="flex flex-col items-center justify-center gap-2 font-sans">
                        <Database className="h-6 w-6 text-fg-4/80" aria-hidden="true" />
                        <p className="text-xs font-medium text-fg-3">No memory facts recorded yet.</p>
                        <p className="text-[11px] text-fg-4 max-w-sm leading-relaxed">
                          Facts are extracted during agent runs and saved into each persona&apos;s <code className="text-fg-3 font-mono">memory.db</code> shard.
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredFacts.map((f) => (
                    <tr key={`${f.persona}-${f.id}`} className="hover:bg-raised/40 transition-colors">
                      <td title={`Fact ID: ${f.id}`} className="px-5 py-3.5 text-fg-4">
                        {f.id}
                      </td>
                      <td
                        title={`Kind: ${f.kind}${f.key ? `, Key: ${f.key}` : ""}`}
                        className="px-5 py-3.5 font-bold text-hue-cyan"
                      >
                        {f.kind}
                        {f.key && <span className="text-fg-4 font-normal"> / {f.key}</span>}
                      </td>
                      <td
                        title={`Fact value: ${f.value}`}
                        className="px-5 py-3.5 font-sans text-xs text-fg leading-relaxed"
                      >
                        {f.value}
                        {f.tags && f.tags.length > 0 && (
                          <span className="ml-2 text-[10px] font-mono text-fg-4">
                            {f.tags.map((t) => `#${t}`).join(" ")}
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          title={`Persona shard: ${f.persona}`}
                          className="px-2 py-0.5 rounded bg-raised text-hue-emerald border border-hue-emerald-line/20 text-[11px]"
                        >
                          {f.persona}
                        </span>
                      </td>
                      <td
                        title={`Updated at: ${timestamp(f.updated_at)}`}
                        className="px-5 py-3.5 text-right text-fg-4 text-[11px]"
                      >
                        {timestamp(f.updated_at)}
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          type="button"
                          onClick={() => {
                            setFactToDelete(f);
                            setDeleteConfirmed(false);
                            setDeleteModalOpen(true);
                          }}
                          title="Delete memory fact"
                          className="text-fg-4 hover:text-rose-400 transition-colors p-1 rounded cursor-pointer"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "observations" && (
        <div
          role="tabpanel"
          id="panel-observations"
          aria-labelledby="tab-observations"
          tabIndex={0}
          className="glass-panel rounded-2xl bg-panel/80 border border-line/80 backdrop-blur-xl overflow-hidden shadow-xl focus:outline-hidden focus-visible:ring-2 focus-visible:ring-accent"
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-sunken/80 text-fg-3 border-b border-line/80 uppercase text-[10px] tracking-wider">
                <tr>
                  <th title="Unique observation identifier" className="px-5 py-3">ID</th>
                  <th title="Source persona database shard" className="px-5 py-3">Shard</th>
                  <th title="Synthesized behavioral observation summary" className="px-5 py-3">Observation</th>
                  <th title="Relative observation weight (significance)" className="px-5 py-3 text-right">Weight</th>
                  <th title="Statistical confidence score percentage" className="px-5 py-3 text-right">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/60 text-fg-2">
                {memory.observations.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-8 text-center">
                      <div className="flex flex-col items-center justify-center gap-2 font-sans">
                        <Lightbulb className="h-6 w-6 text-fg-4/80" aria-hidden="true" />
                        <p className="text-xs font-medium text-fg-3">No observations recorded yet.</p>
                        <p className="text-[11px] text-fg-4 max-w-sm leading-relaxed">
                          Observations summarize learned behaviors and insights synthesized across agent executions.
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  memory.observations.map((o) => (
                    <tr key={`${o.persona}-${o.id}`} className="hover:bg-raised/40 transition-colors">
                      <td title={`Observation ID: ${o.id}`} className="px-5 py-3.5 text-fg-4">
                        {o.id}
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          title={`Persona shard: ${o.persona}`}
                          className="px-2 py-0.5 rounded bg-raised text-hue-violet border border-hue-violet-line/20 text-[11px]"
                        >
                          {o.persona}
                        </span>
                      </td>
                      <td
                        title={`Observation summary: ${o.summary}`}
                        className="px-5 py-3.5 font-sans text-xs text-fg leading-relaxed"
                      >
                        {o.summary}
                      </td>
                      <td
                        title={`Observation weight: ${o.weight.toFixed(2)}`}
                        aria-label={`Observation weight: ${o.weight.toFixed(2)}`}
                        className="px-5 py-3.5 text-right text-hue-amber"
                      >
                        {o.weight.toFixed(2)}
                      </td>
                      <td
                        title={`Confidence score: ${(o.confidence * 100).toFixed(0)}%`}
                        aria-label={`Confidence score: ${(o.confidence * 100).toFixed(0)}%`}
                        className="px-5 py-3.5 text-right text-hue-emerald"
                      >
                        {(o.confidence * 100).toFixed(0)}%
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "simulator" && (
        <div
          role="tabpanel"
          id="panel-simulator"
          aria-labelledby="tab-simulator"
          tabIndex={0}
          className="p-5 rounded-2xl bg-panel border border-line shadow-xs space-y-4 font-mono text-xs focus:outline-hidden"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-line">
            <div>
              <h4 className="text-sm font-bold font-display text-fg flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-hue-emerald" />
                Prompt Injection Simulator
              </h4>
              <p className="text-[11px] text-fg-3 mt-0.5">
                Simulates real-time semantic retrieval and prompt block formatting without calling an LLM
              </p>
            </div>

            <div className="flex items-center gap-2">
              <label htmlFor="sim-persona-select" className="text-[11px] text-fg-3">Persona:</label>
              <select
                id="sim-persona-select"
                value={simPersona}
                onChange={(e) => setSimPersona(e.target.value)}
                className="px-2.5 py-1 rounded-lg bg-canvas border border-line text-xs font-mono text-fg focus:outline-hidden"
              >
                <option value="sakthai">SakThai</option>
                <option value="sakking">SakKing</option>
                <option value="saksee">SakSee</option>
                <option value="sakjules">SakJules</option>
                <option value="saksit">SakSit</option>
                <option value="saktan">SakTan</option>
              </select>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={simQuery}
              onChange={(e) => setSimQuery(e.target.value)}
              placeholder="Enter search context prompt to simulate injection..."
              className="flex-1 px-3 py-2 rounded-xl bg-canvas border border-line text-xs font-mono text-fg focus:outline-hidden focus:border-hue-emerald"
            />
            <button
              type="button"
              onClick={handleRunSimulator}
              disabled={isSimulating || !simQuery.trim()}
              className="px-4 py-2 rounded-xl bg-hue-emerald-tint/70 text-hue-emerald border border-hue-emerald-line text-xs font-mono font-bold hover:bg-hue-emerald-tint cursor-pointer disabled:opacity-50 transition-colors"
            >
              {isSimulating ? "Simulating..." : "Preview"}
            </button>
          </div>

          {simResult && (
            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between text-[11px] text-fg-3">
                <span>Retrieved Context ({simResult.facts.length} facts, {simResult.observations.length} observations)</span>
              </div>
              <pre className="p-4 rounded-xl bg-canvas border border-line text-[11px] font-mono text-fg-2 whitespace-pre-wrap overflow-x-auto leading-relaxed">
                {simResult.prompt_context}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Kind Counts Footer Summary */}
      {Object.keys(memory.kind_counts).length > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
          <span className="text-fg-4 flex items-center gap-1">
            <Layers className="h-3 w-3" aria-hidden="true" /> by kind:
          </span>
          {Object.entries(memory.kind_counts)
            .sort((a, b) => b[1] - a[1])
            .map(([kind, count]) => (
              <span
                key={kind}
                title={`Fact count for kind "${kind}": ${count.toLocaleString()}`}
                className="px-2 py-0.5 rounded-full bg-panel border border-line text-fg-2"
              >
                {kind} <span className="text-hue-cyan">{count}</span>
              </span>
            ))}
        </div>
      )}

      {/* Add Fact Modal */}
      {addModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg bg-panel border border-line rounded-2xl shadow-2xl p-6 space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-line">
              <h4 className="text-sm font-bold font-display text-fg flex items-center gap-2">
                <Plus className="h-4 w-4 text-hue-emerald" />
                Add Persistent Memory Fact
              </h4>
              <button
                type="button"
                onClick={() => setAddModalOpen(false)}
                className="text-fg-3 hover:text-fg cursor-pointer p-1"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {guardrailBlockReason && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5">
                <ShieldAlert className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-bold">DataLossGuardrail Protection:</div>
                  <div className="text-[11px] mt-0.5 text-rose-200">{guardrailBlockReason}</div>
                </div>
              </div>
            )}

            {submitSuccess && (
              <div className="p-3 rounded-xl bg-hue-emerald-tint/40 border border-hue-emerald-line text-hue-emerald text-xs flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>{submitSuccess}</span>
              </div>
            )}

            <form onSubmit={handleAddSubmit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="add-persona-select" className="block text-[11px] text-fg-2 mb-1">Target Persona Shard:</label>
                  <select
                    id="add-persona-select"
                    value={addPersona}
                    onChange={(e) => setAddPersona(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-canvas border border-line text-xs font-mono text-fg focus:outline-hidden"
                  >
                    <option value="sakthai">SakThai</option>
                    <option value="sakking">SakKing</option>
                    <option value="saksee">SakSee</option>
                    <option value="sakjules">SakJules</option>
                    <option value="saksit">SakSit</option>
                    <option value="saktan">SakTan</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="add-kind-select" className="block text-[11px] text-fg-2 mb-1">Fact Kind:</label>
                  <select
                    id="add-kind-select"
                    value={addKind}
                    onChange={(e) => setAddKind(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-canvas border border-line text-xs font-mono text-fg focus:outline-hidden"
                  >
                    <option value="fact">fact</option>
                    <option value="pref">pref</option>
                    <option value="goal">goal</option>
                    <option value="pattern">pattern</option>
                    <option value="note">note</option>
                  </select>
                </div>
              </div>

              <div>
                <label htmlFor="add-key-input" className="block text-[11px] text-fg-2 mb-1">Key (Optional Identifier):</label>
                <input
                  id="add-key-input"
                  type="text"
                  value={addKey}
                  onChange={(e) => setAddKey(e.target.value)}
                  placeholder="e.g. ci_pipeline_runner"
                  className="w-full px-3 py-2 rounded-xl bg-canvas border border-line text-xs font-mono text-fg focus:outline-hidden"
                />
              </div>

              <div>
                <label htmlFor="add-value-textarea" className="block text-[11px] text-fg-2 mb-1">Fact Content / Value:</label>
                <textarea
                  id="add-value-textarea"
                  rows={3}
                  value={addValue}
                  onChange={(e) => setAddValue(e.target.value)}
                  placeholder="Enter fact content to store persistently..."
                  required
                  className="w-full px-3 py-2 rounded-xl bg-canvas border border-line text-xs font-mono text-fg focus:outline-hidden focus:border-hue-emerald"
                />
              </div>

              <div>
                <label htmlFor="add-tags-input" className="block text-[11px] text-fg-2 mb-1">Tags (Comma-separated):</label>
                <input
                  id="add-tags-input"
                  type="text"
                  value={addTags}
                  onChange={(e) => setAddTags(e.target.value)}
                  placeholder="e.g. ci, automation, release"
                  className="w-full px-3 py-2 rounded-xl bg-canvas border border-line text-xs font-mono text-fg focus:outline-hidden"
                />
              </div>

              {approvalToken && (
                <div>
                  <label htmlFor="add-approval-token-input" className="block text-[11px] text-rose-300 mb-1">Approval Authorization Token:</label>
                  <input
                    id="add-approval-token-input"
                    type="text"
                    value={approvalToken}
                    onChange={(e) => setApprovalToken(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-canvas border border-rose-500/40 text-xs font-mono text-rose-200 focus:outline-hidden"
                  />
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-line">
                <button
                  type="button"
                  onClick={() => setAddModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-line text-fg-3 hover:text-fg hover:border-line-strong transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !addValue.trim()}
                  className="px-4 py-2 rounded-xl bg-hue-emerald-tint/70 text-hue-emerald border border-hue-emerald-line hover:bg-hue-emerald-tint transition-colors font-bold cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? "Writing..." : approvalToken ? "Authorize & Write" : "Save Fact"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && factToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-md bg-panel border border-rose-500/30 rounded-2xl shadow-xl p-6 space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-line">
              <h4 className="text-sm font-bold font-display text-rose-400 flex items-center gap-2">
                <Trash2 className="h-4 w-4" />
                Confirm Fact Deletion
              </h4>
              <button
                type="button"
                onClick={() => setDeleteModalOpen(false)}
                className="text-fg-3 hover:text-fg cursor-pointer p-1"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="text-fg-2 text-[11px] leading-relaxed">
              Are you sure you want to permanently remove this fact from the{" "}
              <strong>{factToDelete.persona || selectedShard}</strong> shard?
            </p>

            <div className="p-3 rounded-xl bg-canvas border border-line text-fg text-[11px] max-h-24 overflow-y-auto">
              {factToDelete.value}
            </div>

            <label className="flex items-center gap-2 pt-2 text-[11px] text-fg-2 cursor-pointer">
              <input
                type="checkbox"
                checked={deleteConfirmed}
                onChange={(e) => setDeleteConfirmed(e.target.checked)}
                className="rounded border-line text-rose-500 focus:ring-rose-500"
              />
              <span>I confirm permanent deletion of this memory record</span>
            </label>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-line">
              <button
                type="button"
                onClick={() => setDeleteModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-line text-fg-3 hover:text-fg transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteSubmit}
                disabled={isDeleting || !deleteConfirmed}
                className="px-4 py-2 rounded-xl bg-rose-500/20 text-rose-300 border border-rose-500/40 hover:bg-rose-500/30 transition-colors font-bold cursor-pointer disabled:opacity-50"
              >
                {isDeleting ? "Deleting..." : "Permanently Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MemoryExplorer;
