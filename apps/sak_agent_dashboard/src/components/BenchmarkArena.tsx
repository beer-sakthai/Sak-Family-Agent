"use client";

import { useState } from "react";
import { BenchmarkArenaData, PersonaBenchmarkScore } from "@/lib/types";
import { getBenchmarkArenaData } from "@/lib/benchmarks";
import { Trophy, Zap, Award, BarChart3, DollarSign, CheckCircle2 } from "lucide-react";

export function BenchmarkArena() {
  const [data] = useState<BenchmarkArenaData>(getBenchmarkArenaData());
  const [selectedPersona, setSelectedPersona] = useState<PersonaBenchmarkScore>(data.leaderboard[0]);

  return (
    <section className="space-y-6" data-testid="benchmark-arena-panel">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-emerald-950/40 via-emerald-900/20 to-zinc-900 border border-emerald-800/40 rounded-xl p-5 backdrop-blur-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Joy Stage · 4.0
            </span>
            <span className="text-xs text-zinc-400">Leads: SakThai & SakKing</span>
          </div>
          <h2 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
            <Trophy className="w-6 h-6 text-emerald-400" />
            Benchmark Arena & Multi-Model Leaderboard
          </h2>
          <p className="text-sm text-zinc-400 mt-1 max-w-2xl">
            Live head-to-head performance evaluations across standard reasoning, coding, math, and tool-accuracy datasets.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-zinc-900/80 border border-zinc-800 px-3.5 py-2 rounded-lg text-center">
            <div className="text-xl font-bold text-emerald-400">6</div>
            <div className="text-[11px] text-zinc-400 font-medium uppercase tracking-wider">Agents Evaluated</div>
          </div>
          <div className="bg-zinc-900/80 border border-zinc-800 px-3.5 py-2 rounded-lg text-center">
            <div className="text-xl font-bold text-cyan-400">5</div>
            <div className="text-[11px] text-zinc-400 font-medium uppercase tracking-wider">Benchmark Suites</div>
          </div>
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
            <Award className="w-4 h-4 text-emerald-400" />
            Persona Evaluation Rankings
          </h3>
          <span className="text-xs text-zinc-400">Tested across 17,800+ total eval samples</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-950/60 text-zinc-400 uppercase text-[10px] tracking-wider border-b border-zinc-800">
              <tr>
                <th className="py-3 px-4">Rank & Persona</th>
                <th className="py-3 px-4">Model & Provider</th>
                <th className="py-3 px-4 text-center">MMLU</th>
                <th className="py-3 px-4 text-center">HumanEval</th>
                <th className="py-3 px-4 text-center">GSM8k</th>
                <th className="py-3 px-4 text-center">Tool-Acc</th>
                <th className="py-3 px-4 text-center">Safety</th>
                <th className="py-3 px-4 text-right">Overall</th>
                <th className="py-3 px-4 text-right">Speed & Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {data.leaderboard.map((item, idx) => (
                <tr
                  key={item.personaSlug}
                  onClick={() => setSelectedPersona(item)}
                  className={`hover:bg-zinc-800/40 cursor-pointer transition-colors ${
                    selectedPersona.personaSlug === item.personaSlug ? "bg-emerald-950/20" : ""
                  }`}
                >
                  <td className="py-3 px-4 font-medium text-zinc-200 flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-zinc-800 text-zinc-300 flex items-center justify-center text-[10px] font-bold">
                      #{idx + 1}
                    </span>
                    {item.personaName}
                  </td>
                  <td className="py-3 px-4 text-zinc-400 font-mono text-[11px]">
                    <div>{item.model}</div>
                    <div className="text-[10px] text-zinc-400 uppercase">{item.provider}</div>
                  </td>
                  <td className="py-3 px-4 text-center font-semibold text-zinc-300">{item.categoryScores.MMLU}%</td>
                  <td className="py-3 px-4 text-center font-semibold text-zinc-300">{item.categoryScores.HumanEval}%</td>
                  <td className="py-3 px-4 text-center font-semibold text-zinc-300">{item.categoryScores.GSM8k}%</td>
                  <td className="py-3 px-4 text-center font-semibold text-emerald-400">{item.categoryScores.ToolAccuracy}%</td>
                  <td className="py-3 px-4 text-center font-semibold text-cyan-400">{item.categoryScores.SafetyRefusal}%</td>
                  <td className="py-3 px-4 text-right font-bold text-sm text-emerald-400">
                    {item.overallScore}%
                  </td>
                  <td className="py-3 px-4 text-right text-zinc-400">
                    <div className="text-zinc-300 font-medium">{item.tokensPerSec} t/s</div>
                    <div className="text-[10px] text-zinc-400">
                      {item.costPer1kRuns === 0 ? "Free ($0.00)" : `$${item.costPer1kRuns.toFixed(2)}/1k`}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
