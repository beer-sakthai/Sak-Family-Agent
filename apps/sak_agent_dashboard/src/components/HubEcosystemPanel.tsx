"use client";

import { useState } from "react";
import { HubAsset, HubEcosystemData } from "@/lib/types";
import { SAK_HUB_ASSETS, getHubEcosystemData } from "@/lib/hub";
import { Globe, Layers, Download, Heart, ShieldCheck, Cpu, ExternalLink, Filter } from "lucide-react";

export function HubEcosystemPanel() {
  const [data] = useState<HubEcosystemData>(getHubEcosystemData());
  const [filterType, setFilterType] = useState<"all" | "model" | "dataset" | "space">("all");

  const filteredAssets = data.assets.filter((a) =>
    filterType === "all" ? true : a.type === filterType
  );

  return (
    <section className="space-y-6" data-testid="hub-ecosystem-panel">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-amber-950/40 via-amber-900/20 to-zinc-900 border border-amber-800/40 rounded-xl p-5 backdrop-blur-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
              Dream Stage · 1.0
            </span>
            <span className="text-xs text-zinc-400">Lead: SakThai (HF Master)</span>
          </div>
          <h2 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
            <Globe className="w-6 h-6 text-amber-400" />
            Hugging Face Hub & Ecosystem Registry
          </h2>
          <p className="text-sm text-zinc-400 mt-1 max-w-2xl">
            Live catalog of 19 Sak-Family fine-tuned models, 16 multi-turn eval datasets, and 7 interactive Spaces.
          </p>
        </div>

        {/* Stats Badges */}
        <div className="flex items-center gap-3">
          <div className="bg-zinc-900/80 border border-zinc-800 px-3.5 py-2 rounded-lg text-center">
            <div className="text-xl font-bold text-amber-400">{data.totalModels}</div>
            <div className="text-[11px] text-zinc-400 font-medium uppercase tracking-wider">Models</div>
          </div>
          <div className="bg-zinc-900/80 border border-zinc-800 px-3.5 py-2 rounded-lg text-center">
            <div className="text-xl font-bold text-cyan-400">{data.totalDatasets}</div>
            <div className="text-[11px] text-zinc-400 font-medium uppercase tracking-wider">Datasets</div>
          </div>
          <div className="bg-zinc-900/80 border border-zinc-800 px-3.5 py-2 rounded-lg text-center">
            <div className="text-xl font-bold text-purple-400">{data.totalSpaces}</div>
            <div className="text-[11px] text-zinc-400 font-medium uppercase tracking-wider">Spaces</div>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
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
        <div className="text-xs text-zinc-400">
          Showing <span className="font-semibold text-zinc-200">{filteredAssets.length}</span> assets
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

              <a
                href={asset.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-amber-400 hover:text-amber-300 font-medium"
              >
                View on HF
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
