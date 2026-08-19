'use client';

import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Cpu,
  Zap,
  Activity,
  Send,
  RefreshCw,
  Terminal,
  Layers,
  Radio,
  Sparkles,
} from 'lucide-react';

interface AgentNode {
  id: string;
  name: string;
  role: string;
  color: string;
  x: number;
  y: number;
  status: 'idle' | 'executing' | 'evaluating';
  currentTask: string;
  workload: number;
  tokensProcessed: number;
}

interface MeshLink {
  from: string;
  to: string;
  label: string;
  active: boolean;
}

interface WarRoomEvent {
  id: string;
  timestamp: string;
  source: string;
  target?: string;
  type: 'INFO' | 'HANDOFF' | 'AST_VERIFY' | 'EVAL_PASS';
  message: string;
}

const PERSONA_NODES: AgentNode[] = [
  {
    id: 'sakjules',
    name: 'SakJules',
    role: 'Automation & CI/CD',
    color: '#3b82f6',
    x: 180,
    y: 80,
    status: 'executing',
    currentTask: 'Running G-Eval Quality Flywheel Gate',
    workload: 85,
    tokensProcessed: 14200,
  },
  {
    id: 'saksee',
    name: 'SakSee',
    role: 'Security & Sentinel',
    color: '#10b981',
    x: 420,
    y: 80,
    status: 'evaluating',
    currentTask: 'AST Path Containment & Vulnerability Scan',
    workload: 92,
    tokensProcessed: 9800,
  },
  {
    id: 'sakking',
    name: 'SakKing',
    role: 'Strategy & Orchestration',
    color: '#8b5cf6',
    x: 520,
    y: 240,
    status: 'executing',
    currentTask: 'Coordinating Multi-Agent Mesh Handoffs',
    workload: 78,
    tokensProcessed: 22100,
  },
  {
    id: 'saktan',
    name: 'SakTan',
    role: 'Data & Finance',
    color: '#f59e0b',
    x: 420,
    y: 400,
    status: 'idle',
    currentTask: 'Aggregating Cloud Run Token Cost Matrices',
    workload: 64,
    tokensProcessed: 18500,
  },
  {
    id: 'sakthai',
    name: 'SakThai',
    role: 'Core Architecture',
    color: '#ec4899',
    x: 180,
    y: 400,
    status: 'executing',
    currentTask: 'Vector Memory Sync & Embedding Alignment',
    workload: 88,
    tokensProcessed: 31000,
  },
  {
    id: 'saknoi',
    name: 'SakNoi',
    role: 'Prompt & Creative',
    color: '#06b6d4',
    x: 80,
    y: 240,
    status: 'idle',
    currentTask: 'Distilling Caveman Directives',
    workload: 45,
    tokensProcessed: 8200,
  },
];

const INITIAL_LINKS: MeshLink[] = [
  { from: 'sakking', to: 'sakjules', label: 'Deploy Task', active: true },
  { from: 'sakking', to: 'saksee', label: 'Audit Task', active: true },
  { from: 'saksee', to: 'sakjules', label: 'AST Sign-off', active: true },
  { from: 'sakking', to: 'saktan', label: 'Cost Model', active: false },
  { from: 'sakthai', to: 'sakking', label: 'Memory Context', active: true },
  { from: 'saknoi', to: 'sakthai', label: 'Prompt Spec', active: false },
];

export const AgentWarRoomPanel: React.FC = () => {
  const [nodes, setNodes] = useState<AgentNode[]>(PERSONA_NODES);
  const [links] = useState<MeshLink[]>(INITIAL_LINKS);
  const [selectedNode, setSelectedNode] = useState<AgentNode | null>(PERSONA_NODES[0]);
  const [events, setEvents] = useState<WarRoomEvent[]>([
    {
      id: 'evt-1',
      timestamp: '19:28:10',
      source: 'SakKing',
      target: 'SakJules',
      type: 'HANDOFF',
      message: 'Dispatched CI/CD regression suite for Quality Flywheel track.',
    },
    {
      id: 'evt-2',
      timestamp: '19:28:14',
      source: 'SakSee',
      type: 'AST_VERIFY',
      message: 'Verified AST zero-tolerance security gate. 100% compliant.',
    },
    {
      id: 'evt-3',
      timestamp: '19:28:18',
      source: 'SakJules',
      type: 'EVAL_PASS',
      message: 'Completed Next.js production build and vitest regression suites.',
    },
  ]);

  const [activeBroadcast, setActiveBroadcast] = useState<string | null>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate live fluctuating workloads
      setNodes((prev) =>
        prev.map((n) => ({
          ...n,
          workload: Math.min(100, Math.max(30, n.workload + Math.floor(Math.random() * 9) - 4)),
          tokensProcessed: n.tokensProcessed + Math.floor(Math.random() * 50),
        }))
      );
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const triggerMeshSync = () => {
    setActiveBroadcast('Syncing all 6 agent knowledge graphs & memory nodes...');
    const newEvent: WarRoomEvent = {
      id: `evt-${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      source: 'SakKing',
      type: 'HANDOFF',
      message: 'Broadcast global knowledge synchronization event across all personas.',
    };
    setEvents((prev) => [newEvent, ...prev].slice(0, 20));
    setTimeout(() => setActiveBroadcast(null), 3000);
  };

  const triggerAstAudit = () => {
    setActiveBroadcast('Executing instantaneous AST Sentinel audit across active sessions...');
    const newEvent: WarRoomEvent = {
      id: `evt-${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      source: 'SakSee',
      type: 'AST_VERIFY',
      message: 'Instantaneous AST audit clean: zero leaked tokens or unescaped paths.',
    };
    setEvents((prev) => [newEvent, ...prev].slice(0, 20));
    setTimeout(() => setActiveBroadcast(null), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner Status Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Mesh Mesh Connectivity</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">6 / 6 Active</div>
          <div className="text-[10px] text-emerald-400 mt-1 font-medium">Zero-Latency In-Memory Bus</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Average Fleet Workload</span>
            <Cpu className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">
            {Math.round(nodes.reduce((acc, n) => acc + n.workload, 0) / nodes.length)}%
          </div>
          <div className="text-[10px] text-slate-400 mt-1">Balanced Autonomous Matrix</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>AST Security Sentinel</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">100.0% Guard</div>
          <div className="text-[10px] text-slate-400 mt-1">Strict Path & Shell Isolation</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Tokens Streamed Today</span>
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">
            {(nodes.reduce((acc, n) => acc + n.tokensProcessed, 0) / 1000).toFixed(1)}k
          </div>
          <div className="text-[10px] text-amber-400 mt-1 font-medium">Estimated: $0.18 USD</div>
        </div>
      </div>

      {activeBroadcast && (
        <div className="p-3 bg-cyan-950/70 border border-cyan-600/60 rounded-lg text-xs text-cyan-200 flex items-center gap-2 shadow-md animate-fade-in">
          <Radio className="w-4 h-4 text-cyan-400 animate-pulse flex-shrink-0" />
          <span>{activeBroadcast}</span>
        </div>
      )}

      {/* Main War Room Canvas & Telemetry Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Topology Mesh SVG Graph */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-2">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              Live Multi-Agent Mesh Topology
            </h3>
            <div className="flex items-center gap-2">
              <button
                onClick={triggerMeshSync}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs flex items-center gap-1 border border-slate-700 transition-colors"
              >
                <RefreshCw className="w-3 h-3 text-cyan-400" />
                Sync Nodes
              </button>
              <button
                onClick={triggerAstAudit}
                className="px-2.5 py-1 bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 rounded text-xs flex items-center gap-1 border border-emerald-800/60 transition-colors"
              >
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                Audit AST
              </button>
            </div>
          </div>

          {/* SVG Mesh Visualizer */}
          <div className="relative w-full h-[480px] bg-slate-950/90 rounded-lg border border-slate-800/80 overflow-hidden flex items-center justify-center">
            <svg width="600" height="480" viewBox="0 0 600 480" className="w-full h-full">
              {/* Connecting Lines */}
              {links.map((link, idx) => {
                const src = nodes.find((n) => n.id === link.from);
                const tgt = nodes.find((n) => n.id === link.to);
                if (!src || !tgt) return null;

                const midX = (src.x + tgt.x) / 2;
                const midY = (src.y + tgt.y) / 2;

                return (
                  <g key={idx}>
                    <line
                      x1={src.x}
                      y1={src.y}
                      x2={tgt.x}
                      y2={tgt.y}
                      stroke={link.active ? '#38bdf8' : '#334155'}
                      strokeWidth={link.active ? 2 : 1}
                      strokeDasharray={link.active ? '4,4' : undefined}
                      className={link.active ? 'animate-pulse' : undefined}
                    />
                    {link.active && (
                      <circle
                        cx={midX}
                        cy={midY}
                        r={3}
                        fill="#38bdf8"
                        className="animate-ping"
                      />
                    )}
                  </g>
                );
              })}

              {/* Persona Nodes */}
              {nodes.map((node) => {
                const isSelected = selectedNode?.id === node.id;
                return (
                  <g
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    className="cursor-pointer transition-transform hover:scale-110"
                  >
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={isSelected ? 32 : 26}
                      fill="#0f172a"
                      stroke={node.color}
                      strokeWidth={isSelected ? 3 : 2}
                      className="shadow-lg"
                    />
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={isSelected ? 38 : 30}
                      fill="none"
                      stroke={node.color}
                      strokeWidth="1"
                      strokeOpacity="0.4"
                      className="animate-pulse"
                    />
                    <text
                      x={node.x}
                      y={node.y - 2}
                      textAnchor="middle"
                      dominantBaseline="central"
                      className="text-[11px] font-bold fill-slate-100 font-mono"
                    >
                      {node.name.slice(3)}
                    </text>
                    <text
                      x={node.x}
                      y={node.y + 12}
                      textAnchor="middle"
                      dominantBaseline="central"
                      className="text-[8px] fill-slate-400 font-sans"
                    >
                      {node.workload}%
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Selected Persona State Card */}
          {selectedNode && (
            <div className="mt-3 p-3 bg-slate-950/80 rounded-lg border border-slate-800 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <div className="font-semibold text-slate-200 flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: selectedNode.color }}
                  />
                  <span>{selectedNode.name}</span>
                  <span className="text-[10px] text-slate-400 font-mono">({selectedNode.role})</span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  <span className="text-slate-500 font-mono">Active Task:</span> {selectedNode.currentTask}
                </div>
              </div>
              <div className="flex items-center gap-4 text-[10px] font-mono text-slate-400 flex-shrink-0">
                <div>Workload: <span className="text-cyan-400 font-bold">{selectedNode.workload}%</span></div>
                <div>Tokens: <span className="text-amber-400 font-bold">{selectedNode.tokensProcessed}</span></div>
              </div>
            </div>
          )}
        </div>

        {/* Live Incident & Telemetry Stream */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between space-y-4">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-emerald-400" />
              Live Telemetry & Handoff Stream
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Continuous inter-agent event log
            </p>
          </div>

          <div className="space-y-2.5 flex-1 max-h-[440px] overflow-y-auto pr-1">
            {events.map((evt) => (
              <div
                key={evt.id}
                className="p-3 bg-slate-950/80 rounded-lg border border-slate-800/80 text-xs space-y-1"
              >
                <div className="flex items-center justify-between text-[10px]">
                  <span className="font-mono text-slate-500">{evt.timestamp}</span>
                  <span
                    className={`font-mono px-1.5 py-0.2 rounded text-[9px] font-bold ${
                      evt.type === 'AST_VERIFY'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/40'
                        : evt.type === 'EVAL_PASS'
                        ? 'bg-blue-950 text-blue-400 border border-blue-800/40'
                        : 'bg-purple-950 text-purple-400 border border-purple-800/40'
                    }`}
                  >
                    {evt.type}
                  </span>
                </div>
                <div className="font-semibold text-slate-200 text-[11px]">
                  {evt.source} {evt.target && `→ ${evt.target}`}
                </div>
                <div className="text-[11px] text-slate-400">{evt.message}</div>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[10px] text-slate-500 font-mono">
            <span>Status: Streaming Live</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              Connected
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
