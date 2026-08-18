'use client';

import React, { useState } from 'react';
import { CloudDeploymentManifest, DeploymentTarget } from '../../lib/types';

interface CloudDeploymentBuilderProps {
  initialManifest: CloudDeploymentManifest;
  onGenerateManifest: (target: DeploymentTarget, serviceName: string, region: string) => Promise<CloudDeploymentManifest>;
}

export const CloudDeploymentBuilder: React.FC<CloudDeploymentBuilderProps> = ({
  initialManifest,
  onGenerateManifest,
}) => {
  const [target, setTarget] = useState<DeploymentTarget>(initialManifest.target);
  const [serviceName, setServiceName] = useState(initialManifest.serviceName);
  const [region, setRegion] = useState(initialManifest.region);
  const [manifest, setManifest] = useState<CloudDeploymentManifest>(initialManifest);
  const [viewTab, setViewTab] = useState<'yaml' | 'dockerfile'>('yaml');
  const [copied, setCopied] = useState(false);

  const handleTargetChange = async (newTarget: DeploymentTarget) => {
    setTarget(newTarget);
    const updated = await onGenerateManifest(newTarget, serviceName, region);
    setManifest(updated);
  };

  const handleRefresh = async () => {
    const updated = await onGenerateManifest(target, serviceName, region);
    setManifest(updated);
  };

  const handleCopy = () => {
    const text = viewTab === 'yaml' ? manifest.manifestYaml : manifest.dockerfile;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span>☁️</span> Cloud Run &amp; GKE Deployment Scaffolder
          </h3>
          <p className="text-xs text-slate-400">
            Generates production container manifests, Knative autoscaling configs, and IAM roles.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1.5 rounded bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700"
          >
            <span>{copied ? '✓ Copied' : `📋 Copy ${viewTab.toUpperCase()}`}</span>
          </button>
        </div>
      </div>

      {/* Target Selector & Configs */}
      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <label className="text-[11px] font-medium text-slate-300">Deployment Target</label>
          <div className="mt-1 flex gap-2">
            <button
              type="button"
              onClick={() => handleTargetChange('cloud_run')}
              className={`flex-1 rounded-lg py-2 text-xs font-semibold transition-all ${
                target === 'cloud_run'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              Cloud Run
            </button>
            <button
              type="button"
              onClick={() => handleTargetChange('gke')}
              className={`flex-1 rounded-lg py-2 text-xs font-semibold transition-all ${
                target === 'gke'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              GKE Cluster
            </button>
          </div>
        </div>

        <div>
          <label className="text-[11px] font-medium text-slate-300">Service Name</label>
          <input
            type="text"
            value={serviceName}
            onChange={(e) => setServiceName(e.target.value)}
            onBlur={handleRefresh}
            className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs font-mono text-slate-200 focus:border-blue-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="text-[11px] font-medium text-slate-300">GCP Region</label>
          <input
            type="text"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            onBlur={handleRefresh}
            className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs font-mono text-slate-200 focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Tabs for YAML vs Dockerfile */}
      <div className="mt-4 flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setViewTab('yaml')}
            className={`px-3 py-1 text-xs font-semibold rounded-md ${
              viewTab === 'yaml' ? 'bg-blue-950 text-blue-300 border border-blue-800/50' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {target === 'cloud_run' ? 'service.yaml (Knative)' : 'deployment.yaml (K8s)'}
          </button>
          <button
            type="button"
            onClick={() => setViewTab('dockerfile')}
            className={`px-3 py-1 text-xs font-semibold rounded-md ${
              viewTab === 'dockerfile' ? 'bg-blue-950 text-blue-300 border border-blue-800/50' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Dockerfile (Multi-Stage Hardened)
          </button>
        </div>

        <div className="text-[10px] font-mono text-slate-400">
          CPU: <span className="text-emerald-400">{manifest.cpu}</span> | RAM: <span className="text-emerald-400">{manifest.memory}</span>
        </div>
      </div>

      <div className="mt-3 rounded-lg border border-slate-800 bg-slate-950 p-4 font-mono text-[11px] leading-relaxed text-slate-200 overflow-x-auto max-h-[360px]">
        <pre>{viewTab === 'yaml' ? manifest.manifestYaml : manifest.dockerfile}</pre>
      </div>
    </div>
  );
};
