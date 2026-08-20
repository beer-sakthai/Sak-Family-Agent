"use client";

import { useState } from "react";
import { HubAsset, HubEcosystemData } from "@/lib/types";
import { SAK_HUB_ASSETS, getHubEcosystemData } from "@/lib/hub";
import {
  Globe,
  Layers,
  Download,
  Heart,
  ShieldCheck,
  Cpu,
  ExternalLink,
  Filter,
  Search,
  CheckCircle,
  AlertTriangle,
  FileCode2,
  RefreshCw,
  Zap,
  Activity,
} from "lucide-react";
import {
  CardValidationResult,
  SpaceAlertItem,
  SpaceDiagnostic,
  SpaceTelemetryItem,
  hfEcosystemEngine,
} from "@/lib/hfEcosystemEngine";

export function HubEcosystemPanel() {
  const [data] = useState<HubEcosystemData>(getHubEcosystemData());
  const [filterType, setFilterType] = useState<"all" | "model" | "dataset" | "space">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedAsset, setSelectedAsset] = useState<HubAsset | null>(null);
  const [cardContent, setCardContent] = useState("");
  const [validationResult, setValidationResult] = useState<CardValidationResult | null>(null);
  const [spaceDiag, setSpaceDiag] = useState<SpaceDiagnostic | null>(null);
  const [batchSyncResults, setBatchSyncResults] = useState<
    Array<{ repoId: string; type: string; score: number; valid: boolean }> | null
  >(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [telemetries] = useState<SpaceTelemetryItem[]>(
    hfEcosystemEngine.getSpacesTelemetry()
  );
  const [alerts] = useState<SpaceAlertItem[]>(
    hfEcosystemEngine.getSpaceAlerts()
  );

  const filteredAssets = data.assets.filter((a) => {
    const matchesType = filterType === "all" ? true : a.type === filterType;
    const matchesSearch =
      searchQuery === "" ||
      a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.meta.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesType && matchesSearch;
  });

  const handleValidateCard = () => {
    if (!selectedAsset) return;
    const res = hfEcosystemEngine.validateCard(selectedAsset.repoId, cardContent);
    setValidationResult(res);
  };

  const handleDiagnoseSpace = (asset: HubAsset) => {
    const diag = hfEcosystemEngine.diagnoseSpace(asset.repoId);
    setSpaceDiag(diag);
  };

  const handleHealSpace = (repoId: string, factory: boolean = false) => {
    const res = hfEcosystemEngine.remediateSpace(repoId, factory);
    if (res.success && spaceDiag) {
      setSpaceDiag({
        ...spaceDiag,
        state: "RUNNING",
        healthy: true,
        errorMessage: undefined,
      });
    }
  };

  const handleBatchSyncPreview = () => {
    setIsSyncing(true);
    setTimeout(() => {
      const results = hfEcosystemEngine.previewAllCards();
      setBatchSyncResults(results);
      setIsSyncing(false);
    }, 300);
  };

  const handleOpenValidator = (asset: HubAsset) => {
    setSelectedAsset(asset);
    setCardContent(`---
license: ${asset.meta.license || "apache-2.0"}
pipeline_tag: ${asset.meta.pipelineTag || "text-generation"}
tags:
${asset.meta.tags.map((t) => `  - ${t}`).join("\n")}
---

# ${asset.name}

> House of Sak Autonomous Intelligence · [[Read the story →](https://huggingface.co/Nanthasit/Nanthasit)]

[![HF Downloads](https://img.shields.io/badge/dynamic/json?label=downloads&query=%24.downloads&url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fmodels%2F${asset.repoId})](https://huggingface.co/${asset.repoId})

## What it is
Fine-tuned specialized intelligence for multi-persona execution workflows.

## Evaluation
- Internal benchmark score: 81.2% (internal, not third-party verified; verified: false)

| Model | Size | Role |
|---|---|---|
| context-1.5b-merged | 1.5B | Flagship |
`);
    setValidationResult(null);
  };

  return (
    <section className="space-y-6" data-testid="hub-ecosystem-panel">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-amber-950/40 via-amber-900/20 to-zinc-900 border border-amber-800/40 rounded-xl p-5 backdrop-blur-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
              Phase 1 · Live Remediation
            </span>
            <span className="text-xs text-zinc-400">Lead: SakThai · Automated CI/CD Sync</span>
          </div>
          <h2 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
            <Globe className="w-6 h-6 text-amber-400" />
            Hugging Face Hub & Ecosystem Registry
          </h2>
          <p className="text-sm text-zinc-400 mt-1 max-w-2xl">
            Live catalog of 19 Sak-Family fine-tuned models, 16 multi-turn eval datasets, and 7 interactive Spaces.
          </p>
        </div>

        {/* Action Controls & Badges */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleBatchSyncPreview}
            disabled={isSyncing}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-xs shadow-md shadow-amber-500/20 transition-all cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
            <span>Audit All Cards</span>
          </button>
          <div className="bg-zinc-900/80 border border-zinc-800 px-3 py-1.5 rounded-lg text-center">
            <div className="text-lg font-bold text-amber-400">{data.totalModels}</div>
            <div className="text-[10px] text-zinc-400 font-medium uppercase tracking-wider">Models</div>
          </div>
          <div className="bg-zinc-900/80 border border-zinc-800 px-3 py-1.5 rounded-lg text-center">
            <div className="text-lg font-bold text-cyan-400">{data.totalDatasets}</div>
            <div className="text-[10px] text-zinc-400 font-medium uppercase tracking-wider">Datasets</div>
          </div>
          <div className="bg-zinc-900/80 border border-zinc-800 px-3 py-1.5 rounded-lg text-center">
            <div className="text-lg font-bold text-purple-400">{data.totalSpaces}</div>
            <div className="text-[10px] text-zinc-400 font-medium uppercase tracking-wider">Spaces</div>
          </div>
        </div>
      </div>

      {/* Phase 2: Live Space Monitoring & Telemetry */}
      <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-400" />
            <h3 className="text-sm font-bold text-zinc-200">Space Telemetry & Health Monitor</h3>
          </div>
          <span className="text-[10px] font-mono text-zinc-400 bg-zinc-950 px-2.5 py-1 rounded-full border border-zinc-800">
            Realtime Pulses: 4 Spaces
          </span>
        </div>

        {/* Active Alerts */}
        {alerts.length > 0 && (
          <div className="space-y-2">
            {alerts.map((al) => (
              <div
                key={al.alertId}
                className="p-3 bg-amber-950/30 border border-amber-800/60 rounded-xl flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2 text-amber-300">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                  <span className="font-semibold">[{al.alertType}]</span>
                  <span>{al.message}</span>
                </div>
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-amber-900/50 text-amber-300 border border-amber-700">
                  {al.severity}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Telemetry Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {telemetries.map((t) => (
            <div
              key={t.repoId}
              className="bg-zinc-950/70 border border-zinc-800/80 rounded-xl p-3.5 space-y-2"
            >
              <div className="flex justify-between items-start">
                <div className="font-medium text-xs text-zinc-200 truncate" title={t.repoId}>
                  {t.repoId.split("/")[1] || t.repoId}
                </div>
                <span
                  className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                    t.runtimeStage === "RUNNING"
                      ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                      : "bg-amber-950 text-amber-400 border border-amber-800"
                  }`}
                >
                  {t.runtimeStage}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-zinc-800/50">
                <div>
                  <span className="text-zinc-500 block text-[10px]">CPU</span>
                  <span className="text-zinc-300 font-mono">{t.cpuUsagePct}%</span>
                </div>
                <div>
                  <span className="text-zinc-500 block text-[10px]">Memory</span>
                  <span className="text-zinc-300 font-mono">
                    {Math.round(t.memoryUsageMb)} MB
                  </span>
                </div>
                <div>
                  <span className="text-zinc-500 block text-[10px]">Latency</span>
                  <span className="text-zinc-300 font-mono">{t.httpLatencyMs} ms</span>
                </div>
                <div>
                  <span className="text-zinc-500 block text-[10px]">Hardware</span>
                  <span className="text-purple-400 font-mono text-[10px]">{t.hardwareTier}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Search & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-4 h-4 text-zinc-400 mr-1" />
          {(["all", "model", "dataset", "space"] as const).map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filterType === type
                  ? "bg-amber-500 text-zinc-950 font-semibold shadow-md shadow-amber-500/20"
                  : "bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {type === "all" ? "All Assets" : `${type.charAt(0).toUpperCase() + type.slice(1)}s`}
            </button>
          ))}
        </div>

        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search assets or tags..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 pr-4 py-1.5 text-xs bg-zinc-900 border border-zinc-800 rounded-lg text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-amber-500 w-full sm:w-64"
          />
        </div>
      </div>

      {/* Assets Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAssets.map((asset) => (
          <div
            key={asset.id}
            className="bg-zinc-900/70 border border-zinc-800 hover:border-amber-500/40 rounded-xl p-4 flex flex-col justify-between transition-all hover:shadow-lg hover:shadow-amber-500/5 group"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <span
                  className={`px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded ${
                    asset.type === "model"
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      : asset.type === "dataset"
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                      : "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                  }`}
                >
                  {asset.type}
                </span>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" />
                  {asset.status}
                </span>
              </div>

              <h3 className="text-sm font-bold text-zinc-100 group-hover:text-amber-400 transition-colors break-words">
                {asset.name}
              </h3>

              {/* Tags */}
              <div className="flex flex-wrap gap-1.5 mt-2.5">
                {asset.meta.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-[10px] bg-zinc-800/80 text-zinc-400 px-2 py-0.5 rounded"
                  >
                    #{tag}
                  </span>
                ))}
              </div>

              {/* Quantizations if model */}
              {asset.meta.hasGGUF && asset.meta.quantizations.length > 0 && (
                <div className="mt-3 flex items-center gap-1.5 flex-wrap">
                  <Cpu className="w-3.5 h-3.5 text-zinc-400" />
                  <span className="text-[11px] text-zinc-400">GGUF Quants:</span>
                  {asset.meta.quantizations.map((q) => (
                    <span
                      key={q}
                      className="text-[10px] font-mono bg-zinc-800 text-amber-300 px-1.5 py-0.5 rounded border border-zinc-700"
                    >
                      {q}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Bottom Footer */}
            <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-xs text-zinc-400">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1 text-zinc-300">
                  <Download className="w-3.5 h-3.5 text-zinc-400" />
                  {asset.meta.downloads.toLocaleString()}
                </span>
                <span className="flex items-center gap-1 text-zinc-300">
                  <Heart className="w-3.5 h-3.5 text-rose-400" />
                  {asset.meta.likes}
                </span>
              </div>

              <div className="flex items-center gap-2">
                {asset.type === "space" ? (
                  <button
                    onClick={() => handleDiagnoseSpace(asset)}
                    className="inline-flex items-center gap-1 text-[11px] text-zinc-400 hover:text-purple-400 font-medium"
                    title="Diagnose Space Runtime"
                  >
                    <Activity className="w-3.5 h-3.5" />
                    <span>Diag</span>
                  </button>
                ) : (
                  <button
                    onClick={() => handleOpenValidator(asset)}
                    className="inline-flex items-center gap-1 text-[11px] text-zinc-400 hover:text-amber-400 font-medium"
                    title="Inspect / Validate Card"
                  >
                    <FileCode2 className="w-3.5 h-3.5" />
                    <span>Lint</span>
                  </button>
                )}
                <a
                  href={asset.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-amber-400 hover:text-amber-300 font-medium"
                >
                  HF
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Batch Sync / Linter Modal */}
      {batchSyncResults && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-3xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <RefreshCw className="w-5 h-5 text-amber-400" />
                  Batch Ecosystem Quality Audit (35 Assets)
                </h3>
                <p className="text-xs text-zinc-400">
                  Audited against House of Sak quality guidelines (Dynamic Badges, Single Table, Honest Benchmarks).
                </p>
              </div>
              <button
                onClick={() => setBatchSyncResults(null)}
                className="text-zinc-500 hover:text-zinc-300 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-96 overflow-y-auto pr-1">
              {batchSyncResults.map((res, i) => (
                <div
                  key={i}
                  className="p-2.5 bg-zinc-950 border border-zinc-800 rounded-lg flex items-center justify-between text-xs"
                >
                  <div className="truncate pr-2">
                    <span className="font-mono text-zinc-200">{res.repoId}</span>
                    <span className="text-[10px] text-zinc-500 block uppercase">{res.type}</span>
                  </div>
                  <span
                    className={`font-mono font-bold px-2 py-0.5 rounded text-[11px] ${
                      res.valid
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                    }`}
                  >
                    {res.score}/100
                  </span>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-end pt-2 border-t border-zinc-800">
              <button
                onClick={() => setBatchSyncResults(null)}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-bold text-xs rounded-xl"
              >
                Close Audit Report
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Space Diagnostics Modal */}
      {spaceDiag && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-purple-400" />
                Space Diagnostic: {spaceDiag.repoId}
              </h3>
              <button
                onClick={() => setSpaceDiag(null)}
                className="text-zinc-500 hover:text-zinc-300 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2 bg-zinc-950 p-4 rounded-xl border border-zinc-800 text-xs">
              <div className="flex justify-between">
                <span className="text-zinc-400">Status:</span>
                <span className={`font-bold font-mono ${spaceDiag.healthy ? "text-emerald-400" : "text-amber-400"}`}>
                  {spaceDiag.state}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Hardware:</span>
                <span className="font-mono text-zinc-200">{spaceDiag.hardware}</span>
              </div>
              {spaceDiag.errorMessage && (
                <div className="pt-2 border-t border-zinc-800 text-amber-300">
                  <span className="font-bold block">Diagnosis:</span>
                  {spaceDiag.errorMessage}
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 justify-end">
              <button
                onClick={() => handleHealSpace(spaceDiag.repoId, false)}
                className="px-3.5 py-1.5 bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs rounded-xl flex items-center gap-1.5"
              >
                <Zap className="w-3.5 h-3.5" />
                Restart Container
              </button>
              <button
                onClick={() => handleHealSpace(spaceDiag.repoId, true)}
                className="px-3.5 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-bold text-xs rounded-xl"
              >
                Factory Rebuild
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Model Card Quality Modal */}
      {selectedAsset && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-2xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <FileCode2 className="w-5 h-5 text-amber-400" />
                  Card Linter & Validator: {selectedAsset.name}
                </h3>
                <p className="text-xs text-zinc-400">
                  Enforces House of Sak guidelines (dynamic badges, single family table, honest evals).
                </p>
              </div>
              <button
                onClick={() => setSelectedAsset(null)}
                className="text-zinc-500 hover:text-zinc-300 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <textarea
              rows={8}
              value={cardContent}
              onChange={(e) => setCardContent(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 font-mono text-xs text-zinc-200 focus:outline-none focus:border-amber-500"
            />

            <div className="flex items-center justify-between">
              <button
                onClick={handleValidateCard}
                className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-xs rounded-xl transition-all"
              >
                Run Quality Linter
              </button>

              {validationResult && (
                <span
                  className={`text-xs font-mono font-bold px-3 py-1 rounded-lg border ${
                    validationResult.valid
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                      : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                  }`}
                >
                  Quality Score: {validationResult.score}/100 ({validationResult.valid ? "PASSED" : "FAILED"})
                </span>
              )}
            </div>

            {validationResult && validationResult.issues.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-zinc-800">
                <h4 className="text-xs font-bold text-zinc-300">Linter Findings:</h4>
                {validationResult.issues.map((iss, i) => (
                  <div
                    key={i}
                    className={`p-2.5 rounded-lg text-xs font-mono flex items-start gap-2 ${
                      iss.severity === "error"
                        ? "bg-rose-950/40 text-rose-300 border border-rose-800/60"
                        : "bg-amber-950/40 text-amber-300 border border-amber-800/60"
                    }`}
                  >
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold uppercase text-[10px] block">[{iss.rule}]</span>
                      <span>{iss.message}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
