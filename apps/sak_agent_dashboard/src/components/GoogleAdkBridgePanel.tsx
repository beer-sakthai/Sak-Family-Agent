'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { AdkCodeViewer } from './adk/AdkCodeViewer';
import { CloudDeploymentBuilder } from './adk/CloudDeploymentBuilder';
import { QualityFlywheelGauge } from './adk/QualityFlywheelGauge';
import { AdkObservabilityExplorer } from './adk/AdkObservabilityExplorer';
import {
  AdkAgentSpec,
  AgentRegistryStatus,
  CloudDeploymentManifest,
  DeploymentTarget,
  QualityFlywheelEvalResult,
} from '../lib/types';
import {
  generateCloudDeploymentManifest,
  getAllAdkSpecs,
  getAgentRegistryStatus,
  runQualityFlywheelEvaluation,
} from '../lib/adk/adk_engine';

export const GoogleAdkBridgePanel: React.FC = () => {
  const [agents, setAgents] = useState<AdkAgentSpec[]>(getAllAdkSpecs());
  const [manifest, setManifest] = useState<CloudDeploymentManifest>(generateCloudDeploymentManifest('cloud_run'));
  const [evalResult, setEvalResult] = useState<QualityFlywheelEvalResult>(runQualityFlywheelEvaluation());
  const [registryStatus, setRegistryStatus] = useState<AgentRegistryStatus>(getAgentRegistryStatus());
  const [isEvaluating, setIsEvaluating] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function loadInitialBridgeData() {
      try {
        const res = await fetch('/api/adk/bridge');
        if (res.ok && isMounted) {
          const data = await res.json();
          if (data.agents) setAgents(data.agents);
          if (data.manifest) setManifest(data.manifest);
          if (data.evalResult) setEvalResult(data.evalResult);
          if (data.registryStatus) setRegistryStatus(data.registryStatus);
        }
      } catch {
        // Fallback already populated
      }
    }

    loadInitialBridgeData();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleGenerateManifest = async (target: DeploymentTarget, serviceName: string, region: string): Promise<CloudDeploymentManifest> => {
    try {
      const res = await fetch('/api/adk/bridge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'generate_manifest', target, serviceName, region }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.manifest) {
          setManifest(data.manifest);
          return data.manifest;
        }
      }
    } catch {
      // Fallback
    }
    return generateCloudDeploymentManifest(target, serviceName, region);
  };

  const handleRunEval = async () => {
    setIsEvaluating(true);
    try {
      const res = await fetch('/api/adk/bridge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'run_eval' }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.evalResult) setEvalResult(data.evalResult);
      }
    } catch {
      // Fallback
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-slate-800 bg-gradient-to-r from-blue-950/40 via-slate-900/60 to-emerald-950/40 p-6 backdrop-blur">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">🚀</span>
              <h2 className="text-xl font-bold text-slate-100">Google ADK &amp; Cloud Deployment Bridge</h2>
              <span className="rounded-full bg-blue-500/20 px-2.5 py-0.5 text-xs font-semibold text-blue-300 border border-blue-500/30">
                Track 20260818
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-400 max-w-2xl">
              Enterprise deployment, evaluation, and registry fleet bridge for <strong>Sak-Family</strong>. Generates
              Python ADK agents, manifests for <strong>Cloud Run &amp; GKE</strong>, and scores accuracy via the
              <strong> Quality Flywheel</strong>.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 text-xs">
            <div className="rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-1.5 font-mono text-[11px] text-slate-300">
              <span className="text-slate-500">Registry:</span>{' '}
              <span className="text-emerald-400">
                {registryStatus.publishedToEnterprise ? '✓ Gemini Enterprise' : 'Local'}
              </span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-1.5 font-mono text-[11px] text-slate-300">
              <span className="text-slate-500">Fleet Count:</span>{' '}
              <span className="text-blue-400">{registryStatus.fleetCount} Personas</span>
            </div>
          </div>
        </div>
      </div>

      {/* ADK Code Generator */}
      <AdkCodeViewer agents={agents} />

      {/* Cloud Run / GKE Manifest Scaffolder */}
      <CloudDeploymentBuilder initialManifest={manifest} onGenerateManifest={handleGenerateManifest} />

      {/* Quality Flywheel Evaluation */}
      <QualityFlywheelGauge evalResult={evalResult} onRunEval={handleRunEval} isRunning={isEvaluating} />

      {/* Cloud Trace & BigQuery Observability Suite */}
      <AdkObservabilityExplorer />
    </div>
  );
};
