'use client';

import React, { useState } from 'react';
import {
  A2AServiceRegistration,
  A2ADelegationResult,
  A2ACapabilityDescriptor,
} from '@/lib/a2a/types';
import {
  Network,
  Cpu,
  ShieldCheck,
  Send,
  Radio,
  Clock,
  CheckCircle2,
  XCircle,
  Terminal,
  Activity,
  Layers,
} from 'lucide-react';

interface A2ARegistryExplorerProps {
  fleet: A2AServiceRegistration[];
  delegations: A2ADelegationResult[];
  onDelegateRpc?: (
    from: string,
    to: string,
    capabilityId: string,
    payload: Record<string, unknown>
  ) => Promise<A2ADelegationResult | null>;
}

export const A2ARegistryExplorer: React.FC<A2ARegistryExplorerProps> = ({
  fleet,
  delegations,
  onDelegateRpc,
}) => {
  const [selectedAgentSlug, setSelectedAgentSlug] = useState<string>(fleet[0]?.agentSlug || 'sakjules');
  const [targetAgentSlug, setTargetAgentSlug] = useState<string>('saksee');
  const [selectedCapId, setSelectedCapId] = useState<string>('cap-see-ast');
  const [payloadJson, setPayloadJson] = useState<string>(
    JSON.stringify({ command: 'git log -n 5', targetPath: '.' }, null, 2)
  );
  const [isDispatching, setIsDispatching] = useState<boolean>(false);
  const [lastResult, setLastResult] = useState<A2ADelegationResult | null>(null);

  const activeAgent = fleet.find((a) => a.agentSlug === selectedAgentSlug) || fleet[0];
  const targetAgent = fleet.find((a) => a.agentSlug === targetAgentSlug) || fleet[1];

  const handleExecuteRpc = async () => {
    setIsDispatching(true);
    try {
      let parsedPayload = {};
      try {
        parsedPayload = JSON.parse(payloadJson);
      } catch {
        parsedPayload = { raw: payloadJson };
      }

      if (onDelegateRpc) {
        const res = await onDelegateRpc(
          selectedAgentSlug,
          targetAgentSlug,
          selectedCapId,
          parsedPayload
        );
        if (res) setLastResult(res);
      }
    } finally {
      setIsDispatching(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Fleet Nodes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {fleet.map((agent) => {
          const isSelected = selectedAgentSlug === agent.agentSlug;
          return (
            <div
              key={agent.agentSlug}
              onClick={() => setSelectedAgentSlug(agent.agentSlug)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-slate-800 border-blue-500 ring-1 ring-blue-500/50 shadow-md'
                  : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-blue-400" />
                  <span className="font-semibold text-slate-100 text-sm">{agent.agentName}</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/40">
                  {agent.healthStatus}
                </span>
              </div>

              <div className="text-xs text-slate-400 mb-2">{agent.role}</div>
              <div className="text-[10px] font-mono text-slate-500 truncate mb-3 bg-slate-950 p-1.5 rounded border border-slate-800/60">
                {agent.endpoint}
              </div>

              <div className="grid grid-cols-3 gap-2 text-[10px] text-slate-400 pt-2 border-t border-slate-800">
                <div>
                  <span className="text-slate-500 block">Caps</span>
                  <span className="font-bold text-slate-200">{agent.capabilities.length}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Uptime</span>
                  <span className="font-bold text-slate-200">{(agent.uptimeSeconds / 3600).toFixed(0)}h</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Calls</span>
                  <span className="font-bold text-cyan-400">{agent.totalCallsHandled}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Agent Capabilities & RPC Test Bench */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Capability Manifest */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              {activeAgent?.agentName} Capability Manifest
            </h3>
            <span className="text-[10px] font-mono text-slate-400">v{activeAgent?.version}</span>
          </div>

          <div className="space-y-2.5">
            {activeAgent?.capabilities.map((cap: A2ACapabilityDescriptor) => (
              <div
                key={cap.id}
                className="p-3 bg-slate-950/80 rounded-lg border border-slate-800 text-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200 text-xs">{cap.name}</span>
                  <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-800 text-blue-400">
                    {cap.category}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">{cap.description}</p>
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-1">
                  <span>⏱️ ~{cap.avgLatencyMs}ms</span>
                  <span>⚡ {cap.rateLimitRpm} rpm</span>
                  <span>
                    AST Guard:{' '}
                    <span className={cap.astRequired ? 'text-emerald-400' : 'text-slate-400'}>
                      {cap.astRequired ? 'Enforced' : 'Direct'}
                    </span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RPC Dispatch Test Bench */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                A2A JSON-RPC 2.0 Test Bench
              </h3>
              <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                AST Signed
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-3">
              <div>
                <label className="text-[11px] text-slate-400 font-medium block mb-1">Source Agent:</label>
                <select
                  value={selectedAgentSlug}
                  onChange={(e) => setSelectedAgentSlug(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                >
                  {fleet.map((a) => (
                    <option key={a.agentSlug} value={a.agentSlug}>
                      {a.agentName}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] text-slate-400 font-medium block mb-1">Target Agent:</label>
                <select
                  value={targetAgentSlug}
                  onChange={(e) => {
                    setTargetAgentSlug(e.target.value);
                    const newTarget = fleet.find((a) => a.agentSlug === e.target.value);
                    if (newTarget && newTarget.capabilities.length > 0) {
                      setSelectedCapId(newTarget.capabilities[0].id);
                    }
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                >
                  {fleet.map((a) => (
                    <option key={a.agentSlug} value={a.agentSlug}>
                      {a.agentName}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mb-3">
              <label className="text-[11px] text-slate-400 font-medium block mb-1">Target Capability:</label>
              <select
                value={selectedCapId}
                onChange={(e) => setSelectedCapId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
              >
                {targetAgent?.capabilities.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.id})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[11px] text-slate-400 font-medium block mb-1">JSON Parameters:</label>
              <textarea
                rows={4}
                value={payloadJson}
                onChange={(e) => setPayloadJson(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 font-mono text-xs text-slate-300 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <button
              onClick={handleExecuteRpc}
              disabled={isDispatching}
              className={`w-full py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-md transition-all ${
                isDispatching
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-500 text-white hover:shadow-blue-500/20'
              }`}
            >
              {isDispatching ? (
                <>
                  <Clock className="w-4 h-4 animate-spin text-blue-300" />
                  Dispatching RPC Call...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 text-cyan-300" />
                  Dispatch A2A Remote Procedure Call
                </>
              )}
            </button>

            {lastResult && (
              <div className="mt-3 p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="font-mono text-slate-400">Status: {lastResult.status.toUpperCase()}</span>
                  <span className="font-mono text-emerald-400">⏱️ {lastResult.executionTimeMs}ms</span>
                </div>
                <div className="font-mono text-[11px] text-slate-300 truncate">
                  {lastResult.result ? JSON.stringify(lastResult.result) : lastResult.error}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Inter-Agent Delegation Log */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Radio className="w-4 h-4 text-emerald-400" />
            Inter-Agent Delegation Telemetry Log
          </h3>
          <span className="text-xs text-slate-500">{delegations.length} calls recorded</span>
        </div>

        <div className="space-y-2">
          {delegations.map((del) => (
            <div
              key={del.delegationId}
              className="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex items-center justify-between text-xs"
            >
              <div className="flex items-center gap-3">
                {del.status === 'success' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                )}
                <div>
                  <div className="font-semibold text-slate-200 flex items-center gap-2">
                    <span className="font-mono text-blue-400">[{del.agentFrom}]</span>
                    <span>→</span>
                    <span className="font-mono text-purple-400">[{del.agentTo}]</span>
                    <span className="text-slate-300 font-sans">{del.method}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                    {del.correlationId} · {new Date(del.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>

              <div className="text-right font-mono text-[11px] text-slate-400 flex-shrink-0">
                <span className="text-emerald-400">{del.executionTimeMs}ms</span>
                {del.astAudited && (
                  <span className="ml-2 text-[9px] bg-slate-800 text-emerald-400 px-1 py-0.2 rounded border border-emerald-800/40">
                    AST OK
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
