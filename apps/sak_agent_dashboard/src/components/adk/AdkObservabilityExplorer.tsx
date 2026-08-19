'use client';

import React, { useState } from 'react';
import {
  OtelTraceSpan,
  TraceWaterfallSummary,
  BigQueryAgentAnalyticsEvent,
  ObservabilityTierConfig,
} from '@/lib/adk/observability_types';
import { AdkObservabilityEngine } from '@/lib/adk/observability_engine';
import {
  Telescope,
  Activity,
  Database,
  CheckCircle2,
  Copy,
  Terminal,
  FileCode2,
  ShieldCheck,
  Play,
  RefreshCw,
  Sparkles,
} from 'lucide-react';

export const AdkObservabilityExplorer: React.FC = () => {
  const [tierConfig] = useState<ObservabilityTierConfig>(
    AdkObservabilityEngine.defaultTierConfig
  );
  const [selectedScenario, setSelectedScenario] = useState<string>('geval_security');
  const [waterfall, setWaterfall] = useState<TraceWaterfallSummary>(
    AdkObservabilityEngine.generateSampleTraceWaterfall('geval_security')
  );
  const [bqEvents] = useState<BigQueryAgentAnalyticsEvent[]>(
    AdkObservabilityEngine.getBigQueryAnalyticsEvents()
  );
  const [activeTab, setActiveTab] = useState<'trace' | 'analytics' | 'terraform'>('trace');
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [copiedText, setCopiedText] = useState<string | null>(null);

  const envVars = AdkObservabilityEngine.generateObservabilityEnvVars(tierConfig);
  const tfSnippet = AdkObservabilityEngine.generateTerraformTelemetrySnippet(tierConfig);

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(label);
    setTimeout(() => setCopiedText(null), 2500);
  };

  const handleSimulateTrace = async (scenarioId = selectedScenario) => {
    setIsSimulating(true);
    setStatusMessage('Emitting OpenTelemetry spans & routing GenAI completion logs to GCS/BigQuery...');
    await new Promise((r) => setTimeout(r, 600));

    const newWaterfall = AdkObservabilityEngine.generateSampleTraceWaterfall(scenarioId);
    setWaterfall(newWaterfall);
    setIsSimulating(false);
    setStatusMessage(`Trace simulation completed: ${newWaterfall.totalSpans} spans captured across ${newWaterfall.totalDurationMs}ms!`);
    setTimeout(() => setStatusMessage(null), 3500);
  };

  const handleScenarioChange = (scenarioId: string) => {
    setSelectedScenario(scenarioId);
    handleSimulateTrace(scenarioId);
  };

  const renderSpan = (span: OtelTraceSpan, depth = 0) => {
    const durationPercent = Math.min(100, Math.max(8, (span.durationMs / waterfall.totalDurationMs) * 100));
    const offsetPercent = Math.min(90, (span.startTimeMs / waterfall.totalDurationMs) * 100);

    return (
      <div key={span.spanId} className="space-y-1.5">
        <div
          className={`p-2.5 rounded-lg border text-xs flex flex-col md:flex-row md:items-center justify-between gap-2 transition-colors ${
            span.kind === 'invoke_workflow'
              ? 'bg-purple-950/40 border-purple-800/60'
              : span.kind === 'invoke_agent'
              ? 'bg-blue-950/40 border-blue-800/60'
              : span.kind === 'execute_tool'
              ? 'bg-emerald-950/40 border-emerald-800/60'
              : 'bg-slate-900 border-slate-800'
          }`}
          style={{ marginLeft: `${depth * 16}px` }}
        >
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <span
              className={`text-[9px] font-mono px-1.5 py-0.2 rounded font-bold uppercase ${
                span.kind === 'invoke_workflow'
                  ? 'bg-purple-900 text-purple-200'
                  : span.kind === 'invoke_agent'
                  ? 'bg-blue-900 text-blue-200'
                  : span.kind === 'execute_tool'
                  ? 'bg-emerald-900 text-emerald-200'
                  : 'bg-slate-800 text-slate-300'
              }`}
            >
              {span.kind}
            </span>
            <span className="font-semibold text-slate-200 truncate">{span.name}</span>
          </div>

          {/* Timeline Bar Visualizer */}
          <div className="w-full md:w-48 bg-slate-950 rounded-full h-2 overflow-hidden flex-shrink-0 border border-slate-800">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                span.kind === 'execute_tool' ? 'bg-emerald-400' : 'bg-cyan-400'
              }`}
              style={{
                marginLeft: `${offsetPercent}%`,
                width: `${durationPercent}%`,
              }}
            />
          </div>

          <div className="flex items-center gap-3 font-mono text-[10px] text-slate-400 flex-shrink-0 justify-between md:justify-end">
            <span>⏱️ {span.durationMs}ms</span>
            {span.attributes.totalTokens && (
              <span className="text-amber-400 font-bold">
                {span.attributes.totalTokens} tokens
              </span>
            )}
            {span.attributes.costUsd && (
              <span className="text-emerald-400">
                +${span.attributes.costUsd.toFixed(4)}
              </span>
            )}
          </div>
        </div>

        {span.children && span.children.map((child) => renderSpan(child, depth + 1))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Banner Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Cloud Trace OpenTelemetry</span>
            <Telescope className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">Active</div>
          <div className="text-[10px] text-emerald-400 mt-1 font-medium">Distributed Span Waterfall</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>BigQuery Agent Analytics</span>
            <Database className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">Enabled</div>
          <div className="text-[10px] text-purple-300 mt-1">{tierConfig.bqDatasetId}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Prompt-Response Logging</span>
            <FileCode2 className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-300 mt-2">GCS Sink</div>
          <div className="text-[10px] text-slate-400 mt-1 truncate">{tierConfig.logsBucketName}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Semconv Capture Level</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-emerald-400 mt-2 font-mono">{tierConfig.semconvLevel}</div>
          <div className="text-[10px] text-slate-400 mt-1">Zero Span Data Leakage</div>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 bg-cyan-950/70 border border-cyan-600/60 rounded-lg text-xs text-cyan-200 flex items-center gap-2 shadow-md">
          <Activity className="w-4 h-4 text-cyan-400 animate-pulse flex-shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Scenario Bar & Action Triggers */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow">
        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
          <span className="text-xs font-semibold text-slate-400">Simulation Scenario:</span>
          <select
            value={selectedScenario}
            onChange={(e) => handleScenarioChange(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            {AdkObservabilityEngine.simulationScenarios.map((sc) => (
              <option key={sc.id} value={sc.id}>
                {sc.title}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={() => handleSimulateTrace()}
          disabled={isSimulating}
          className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow transition-all ${
            isSimulating
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-cyan-600 hover:bg-cyan-500 text-white'
          }`}
        >
          {isSimulating ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              Simulating Trace...
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              Run Trace Simulation
            </>
          )}
        </button>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('trace')}
          className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
            activeTab === 'trace'
              ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/60 shadow'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Telescope className="w-4 h-4 text-cyan-400" />
          Cloud Trace Waterfall
        </button>

        <button
          onClick={() => setActiveTab('analytics')}
          className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
            activeTab === 'analytics'
              ? 'bg-purple-950 text-purple-300 border border-purple-800/60 shadow'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Database className="w-4 h-4 text-purple-400" />
          BigQuery Analytics Stream
        </button>

        <button
          onClick={() => setActiveTab('terraform')}
          className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
            activeTab === 'terraform'
              ? 'bg-amber-950 text-amber-300 border border-amber-800/60 shadow'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileCode2 className="w-4 h-4 text-amber-400" />
          Terraform &amp; Env Vars
        </button>
      </div>

      {/* Tab 1: Cloud Trace Waterfall */}
      {activeTab === 'trace' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                Live OpenTelemetry Span Hierarchy: {waterfall.rootWorkflow}
              </h3>
              <div className="text-[11px] text-slate-400 mt-0.5">
                Trace ID: <span className="font-mono text-cyan-300">{waterfall.traceId}</span>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono text-slate-300">
              <div>Total: <span className="text-cyan-400 font-bold">{waterfall.totalDurationMs}ms</span></div>
              <div>Tokens: <span className="text-amber-400 font-bold">{waterfall.totalTokens}</span></div>
              <div>Cost: <span className="text-emerald-400 font-bold">${waterfall.totalCostUsd}</span></div>
            </div>
          </div>

          <div className="space-y-2">
            {waterfall.spans.map((root) => renderSpan(root))}
          </div>
        </div>
      )}

      {/* Tab 2: BigQuery Analytics Stream */}
      {activeTab === 'analytics' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Database className="w-4 h-4 text-purple-400" />
              BigQuery Agent Analytics Telemetry Table
            </h3>
            <span className="text-[10px] font-mono text-purple-300">Dataset: {tierConfig.bqDatasetId}</span>
          </div>

          <div className="space-y-2.5">
            {bqEvents.map((evt) => (
              <div
                key={evt.eventId}
                className="p-3 bg-slate-950/80 rounded-lg border border-slate-800 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] px-1.5 py-0.2 rounded bg-purple-950 text-purple-300 border border-purple-800/40 uppercase font-bold">
                      {evt.eventType}
                    </span>
                    <span className="font-semibold text-slate-200">{evt.agentSlug}</span>
                    <span className="text-slate-500 font-mono text-[10px]">({evt.model})</span>
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-1 truncate">
                    {evt.gcsLogUri}
                  </div>
                </div>

                <div className="flex items-center gap-4 text-right font-mono text-[10px] text-slate-400 flex-shrink-0">
                  <div>⏱️ {evt.latencyMs}ms</div>
                  <div>⚡ {evt.totalTokens} tok</div>
                  <div className="text-emerald-400 font-bold">+${evt.costUsd.toFixed(4)}</div>
                  {evt.astCompliant && (
                    <span className="px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/40 text-[9px]">
                      AST OK
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Terraform & Environment Variables */}
      {activeTab === 'terraform' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Environment Variables */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                ADK Production Environment Variables
              </h3>
              <button
                onClick={() =>
                  handleCopy(
                    Object.entries(envVars)
                      .map(([k, v]) => `${k}=${v}`)
                      .join('\n'),
                    'env'
                  )
                }
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs flex items-center gap-1 border border-slate-700"
              >
                <Copy className="w-3 h-3 text-cyan-400" />
                {copiedText === 'env' ? 'Copied!' : 'Copy .env'}
              </button>
            </div>

            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-slate-300 space-y-2">
              {Object.entries(envVars).map(([key, val]) => (
                <div key={key} className="break-all">
                  <span className="text-cyan-400 font-bold">{key}</span>=<span className="text-amber-300">{val}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Terraform HCL Snippet */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <FileCode2 className="w-4 h-4 text-amber-400" />
                Terraform Telemetry Resource Module
              </h3>
              <button
                onClick={() => handleCopy(tfSnippet, 'tf')}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs flex items-center gap-1 border border-slate-700"
              >
                <Copy className="w-3 h-3 text-amber-400" />
                {copiedText === 'tf' ? 'Copied!' : 'Copy HCL'}
              </button>
            </div>

            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap max-h-64 overflow-y-auto">
              {tfSnippet}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
