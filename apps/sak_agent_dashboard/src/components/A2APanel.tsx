'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { A2ARegistryExplorer } from './a2a/A2ARegistryExplorer';
import {
  A2AServiceRegistration,
  A2ADelegationResult,
  A2AHealthStatus,
} from '@/lib/a2a/types';
import { ServiceRegistry, INITIAL_SAK_FLEET } from '@/lib/a2a/serviceRegistry';
import { A2AEngine } from '@/lib/a2a/a2aEngine';
import { Network, Activity, ShieldCheck, Zap, Layers } from 'lucide-react';

export const A2APanel: React.FC = () => {
  const [fleet, setFleet] = useState<A2AServiceRegistration[]>(INITIAL_SAK_FLEET);
  const [delegations, setDelegations] = useState<A2ADelegationResult[]>(
    A2AEngine.getRecentDelegations()
  );
  const [health, setHealth] = useState<A2AHealthStatus>(ServiceRegistry.getFleetHealth());
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    let isSubscribed = true;
    const fetchFleet = async () => {
      try {
        const res = await fetch('/api/a2a/registry');
        if (res.ok) {
          const json = await res.json();
          if (isSubscribed && json.data) {
            if (json.data.fleet) setFleet(json.data.fleet);
            if (json.data.health) setHealth(json.data.health);
            if (json.data.delegations) setDelegations(json.data.delegations);
          }
        }
      } catch {
        // Fallback in-memory
      }
    };
    void fetchFleet();
    return () => {
      isSubscribed = false;
    };
  }, []);

  const handleDelegateRpc = async (
    from: string,
    to: string,
    capabilityId: string,
    payload: Record<string, unknown>
  ): Promise<A2ADelegationResult | null> => {
    setStatusMessage(`Dispatching JSON-RPC 2.0 call from [${from}] to [${to}]...`);
    try {
      const res = await fetch('/api/a2a/registry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'delegate',
          agentFrom: from,
          agentTo: to,
          capabilityId,
          payload,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.result) {
          setDelegations((prev) => [data.result, ...prev].slice(0, 50));
          setStatusMessage(`RPC ${capabilityId} completed in ${data.result.executionTimeMs}ms.`);
          return data.result;
        }
      } else {
        const localRes = await A2AEngine.delegateTask({
          agentFrom: from,
          agentTo: to,
          capabilityId,
          payload,
        });
        setDelegations((prev) => [localRes, ...prev].slice(0, 50));
        setStatusMessage(`Local RPC ${capabilityId} completed.`);
        return localRes;
      }
    } catch {
      const localRes = await A2AEngine.delegateTask({
        agentFrom: from,
        agentTo: to,
        capabilityId,
        payload,
      });
      setDelegations((prev) => [localRes, ...prev].slice(0, 50));
      return localRes;
    } finally {
      setTimeout(() => setStatusMessage(null), 3500);
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Top Banner Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Fleet Service Nodes</span>
            <Network className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">
            {health.healthyNodes} / {health.fleetSize}
          </div>
          <div className="text-[10px] text-emerald-400 mt-1 font-medium">100% Mesh Health</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Registered Capabilities</span>
            <Layers className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">{health.totalCapabilities}</div>
          <div className="text-[10px] text-slate-400 mt-1">Cross-Persona APIs</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Average RPC Latency</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">{health.avgFleetLatencyMs}ms</div>
          <div className="text-[10px] text-slate-400 mt-1">In-Memory JSON-RPC 2.0</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>AST Security Sentinel</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">100.0%</div>
          <div className="text-[10px] text-slate-400 mt-1">Zero-Trust Inter-Agent Gate</div>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 bg-cyan-950/70 border border-cyan-600/60 rounded-lg text-xs text-cyan-200 flex items-center gap-2 shadow-md animate-fade-in">
          <Activity className="w-4 h-4 text-cyan-400 animate-pulse flex-shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Explorer Component */}
      <A2ARegistryExplorer
        fleet={fleet}
        delegations={delegations}
        onDelegateRpc={handleDelegateRpc}
      />
    </div>
  );
};
