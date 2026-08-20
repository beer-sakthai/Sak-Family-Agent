"use client";

import React, { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { MetricsData, AgentPersona } from "@/lib/types";
import { BarChart3, TrendingUp, Zap, PieChart as PieIcon } from "lucide-react";

interface AnalyticsChartsProps {
  metrics: MetricsData;
  agents?: AgentPersona[];
}

const COLORS = ["#06b6d4", "#10b981", "#8b5cf6", "#f59e0b", "#f43f5e"];

export function AnalyticsCharts({ metrics, agents }: AnalyticsChartsProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-shot client-mount flag to gate SSR-unsafe Recharts
    setIsMounted(true);
  }, []);

  // Benchmark data for personas
  const benchmarkData = (agents && agents.length > 0)
    ? agents.map((a) => ({
        name: a.name,
        score: a.benchmarkScore ?? 90,
        latency: a.latencyMs,
      }))
    : [
        { name: "SakThai", score: 96.5, latency: 320 },
        { name: "SakKing", score: 94.2, latency: 540 },
        { name: "SakSee", score: 91.8, latency: 410 },
        { name: "SakSit", score: 98.0, latency: 290 },
        { name: "SakJules", score: 93.5, latency: 380 },
      ];

  // Token Stats Breakdown
  const tokenBreakdown = [
    { name: "Prompt Tokens", value: metrics?.tokenStats?.promptTokens || 950000 },
    { name: "Completion Tokens", value: metrics?.tokenStats?.completionTokens || 500000 },
  ];

  // Stop Reasons Breakdown for Pie Chart
  const stopReasonData = metrics?.stopReasons
    ? Object.entries(metrics.stopReasons).map(([key, val]) => ({
        name: key,
        value: val,
      }))
    : [
        { name: "end_turn", value: 740 },
        { name: "max_tokens", value: 21 },
      ];

  // Trend lines data
  const trendData = (metrics?.trends && metrics.trends.length > 0)
    ? metrics.trends
    : [
        { date: "Day 1", runs: 120, latencyMs: 340 },
        { date: "Day 2", runs: 180, latencyMs: 390 },
        { date: "Day 3", runs: 210, latencyMs: 370 },
        { date: "Day 4", runs: 250, latencyMs: 410 },
        { date: "Day 5", runs: 300, latencyMs: 388 },
      ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold font-display text-white tracking-tight">
            Performance & Benchmark Analytics
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Interactive performance charts, token distribution, latency trends, and execution metrics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-cyan-400">
            Total Runs: <strong className="text-white">{metrics?.totalRuns ?? 761} total</strong>
          </span>
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-emerald-400">
            Success Rate: <strong className="text-white">{((metrics?.successRate ?? 0.985) * 100).toFixed(1)}%</strong>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. Benchmark Scores per Persona (Bar Chart) */}
        <div className="glass-panel p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <BarChart3 className="h-4 w-4" />
              </div>
              <h4 className="text-sm font-bold font-display text-slate-200">
                Persona Benchmark Scores (%)
              </h4>
            </div>
            <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">
              eval.jsonl
            </span>
          </div>

          <div className="h-64 w-full">
            {isMounted && (
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <BarChart data={benchmarkData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} domain={[70, 100]} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "0.5rem", color: "#f8fafc" }}
                  />
                  <Bar dataKey="score" fill="#06b6d4" radius={[6, 6, 0, 0]} name="Score %" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* 2. Token Usage Distribution (Area Chart) */}
        <div className="glass-panel p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Zap className="h-4 w-4" />
              </div>
              <h4 className="text-sm font-bold font-display text-slate-200">
                Token Usage & Consumption
              </h4>
            </div>
            <span className="text-xs font-mono text-emerald-400">
              Total: {(metrics?.tokenStats?.totalTokens ?? 1450000).toLocaleString()} tokens
            </span>
          </div>

          <div className="h-64 w-full">
            {isMounted && (
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <AreaChart data={tokenBreakdown} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="tokenGlow" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "0.5rem", color: "#f8fafc" }}
                  />
                  <Area type="monotone" dataKey="value" stroke="#10b981" fillOpacity={1} fill="url(#tokenGlow)" name="Tokens" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* 3. Latency Trends (Line Chart) */}
        <div className="glass-panel p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <TrendingUp className="h-4 w-4" />
              </div>
              <h4 className="text-sm font-bold font-display text-slate-200">
                Latency Trends (ms)
              </h4>
            </div>
            <span className="text-xs font-mono text-cyan-300">
              Avg: {metrics?.avgLatencyMs ?? 388}ms
            </span>
          </div>

          <div className="h-64 w-full">
            {isMounted && (
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <LineChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "0.5rem", color: "#f8fafc" }}
                  />
                  <Line type="monotone" dataKey="latencyMs" stroke="#06b6d4" strokeWidth={3} dot={{ r: 4, fill: "#06b6d4" }} name="Latency (ms)" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* 4. Stop Reason Breakdown (Pie Chart) */}
        <div className="glass-panel p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <PieIcon className="h-4 w-4" />
              </div>
              <h4 className="text-sm font-bold font-display text-slate-200">
                Stop Reason Breakdown
              </h4>
            </div>
            <span className="text-xs font-mono text-purple-400">
              {stopReasonData.length} Reasons Captured
            </span>
          </div>

          <div className="h-64 w-full flex items-center justify-center">
            {isMounted && (
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <PieChart>
                  <Pie
                    data={stopReasonData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="value"
                    nameKey="name"
                  >
                    {stopReasonData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "0.5rem", color: "#f8fafc" }}
                  />
                  <Legend
                    formatter={(value) => <span className="text-xs font-mono text-slate-300">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default AnalyticsCharts;
