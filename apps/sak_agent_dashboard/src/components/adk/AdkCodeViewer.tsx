'use client';

import React, { useState } from 'react';
import { AdkAgentSpec } from '../../lib/types';

interface AdkCodeViewerProps {
  agents: AdkAgentSpec[];
}

export const AdkCodeViewer: React.FC<AdkCodeViewerProps> = ({ agents }) => {
  const [selectedPersona, setSelectedPersona] = useState<string>(agents[0]?.personaSlug || 'sakthai');
  const [copied, setCopied] = useState(false);

  const currentAgent = agents.find((a) => a.personaSlug === selectedPersona) || agents[0];

  const handleCopy = () => {
    if (currentAgent) {
      navigator.clipboard.writeText(currentAgent.generatedPythonCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span>🐍</span> Google ADK Agent Code Generator
          </h3>
          <p className="text-xs text-slate-400">
            Standardized Python ADK definitions with typed tools, OpenTelemetry tracing, and session persistence.
          </p>
        </div>

        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700"
        >
          <span>{copied ? '✓ Copied' : '📋 Copy Python Script'}</span>
        </button>
      </div>

      {/* Persona Pill Selector */}
      <div className="mt-4 flex flex-wrap gap-2">
        {agents.map((agent) => (
          <button
            key={agent.personaSlug}
            type="button"
            onClick={() => setSelectedPersona(agent.personaSlug)}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              selectedPersona === agent.personaSlug
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            {agent.name}
          </button>
        ))}
      </div>

      {currentAgent && (
        <div className="mt-4">
          <div className="flex flex-wrap gap-2 text-xs text-slate-400 mb-2">
            <span>Model: <strong className="text-blue-300 font-mono">{currentAgent.model}</strong></span>
            <span>•</span>
            <span>Primitive: <strong className="text-purple-300 font-mono">{currentAgent.primitive}</strong></span>
            <span>•</span>
            <span>Tools: <strong className="text-emerald-300 font-mono">{currentAgent.tools.join(', ')}</strong></span>
          </div>

          <div className="relative rounded-lg border border-slate-800 bg-slate-950 p-4 font-mono text-[11px] leading-relaxed text-slate-200 overflow-x-auto max-h-[380px]">
            <pre>{currentAgent.generatedPythonCode}</pre>
          </div>
        </div>
      )}
    </div>
  );
};
