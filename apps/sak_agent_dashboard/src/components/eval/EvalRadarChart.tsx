'use client';

import React from 'react';
import { PersonaBenchmarkSummary } from '@/lib/eval/types';

interface EvalRadarChartProps {
  summaries: PersonaBenchmarkSummary[];
  selectedPersona?: string;
  onSelectPersona?: (slug: string) => void;
}

export const EvalRadarChart: React.FC<EvalRadarChartProps> = ({
  summaries,
  selectedPersona,
  onSelectPersona,
}) => {
  const dimensions = [
    { key: 'avgGoalCompletion', label: 'Goal Completion', angle: 0 },
    { key: 'avgToolPrecision', label: 'Tool Precision', angle: 90 },
    { key: 'avgSafetyCompliance', label: 'AST Safety', angle: 180 },
    { key: 'efficiency', label: 'Cost/Latency Efficiency', angle: 270 },
  ];

  const size = 300;
  const center = size / 2;
  const radius = 100;

  const getCoordinates = (value: number, angleDeg: number) => {
    const angleRad = (angleDeg - 90) * (Math.PI / 180);
    const r = (Math.max(10, Math.min(100, value)) / 100) * radius;
    return {
      x: center + r * Math.cos(angleRad),
      y: center + r * Math.sin(angleRad),
    };
  };

  const colors = [
    '#3b82f6', // Blue (Jules)
    '#10b981', // Emerald (See)
    '#8b5cf6', // Purple (King)
    '#f59e0b', // Amber (Tan)
    '#ec4899', // Pink (Thai)
    '#06b6d4', // Cyan (Noi)
  ];

  const activeSummary = summaries.find((s) => s.personaSlug === selectedPersona) || summaries[0];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col md:flex-row gap-6 items-center">
      {/* Radar SVG Area */}
      <div className="relative flex flex-col items-center">
        <h4 className="text-sm font-semibold text-slate-300 mb-2">Multi-Dimensional Evaluation Radar</h4>
        <svg width={size} height={size} className="overflow-visible">
          {/* Grid Background Circles */}
          {[0.25, 0.5, 0.75, 1.0].map((ratio, idx) => (
            <circle
              key={idx}
              cx={center}
              cy={center}
              r={radius * ratio}
              fill="none"
              stroke="#334155"
              strokeDasharray={ratio < 1 ? '3,3' : undefined}
              strokeWidth="1"
            />
          ))}

          {/* Grid Axes */}
          {dimensions.map((dim, idx) => {
            const end = getCoordinates(100, dim.angle);
            return (
              <line
                key={idx}
                x1={center}
                y1={center}
                x2={end.x}
                y2={end.y}
                stroke="#475569"
                strokeWidth="1"
              />
            );
          })}

          {/* Axis Labels */}
          {dimensions.map((dim, idx) => {
            const pos = getCoordinates(120, dim.angle);
            return (
              <text
                key={idx}
                x={pos.x}
                y={pos.y}
                textAnchor="middle"
                dominantBaseline="central"
                className="text-[10px] fill-slate-400 font-medium"
              >
                {dim.label}
              </text>
            );
          })}

          {/* Persona Polygons */}
          {summaries.map((summary, idx) => {
            const isSelected = !selectedPersona || selectedPersona === summary.personaSlug || selectedPersona === 'all';
            if (!isSelected) return null;

            const values = [
              summary.avgGoalCompletion,
              summary.avgToolPrecision,
              summary.avgSafetyCompliance,
              Math.max(30, 100 - summary.avgLatencyMs / 50),
            ];

            const points = dimensions
              .map((dim, dIdx) => {
                const pt = getCoordinates(values[dIdx], dim.angle);
                return `${pt.x},${pt.y}`;
              })
              .join(' ');

            const color = colors[idx % colors.length];

            return (
              <g key={summary.personaSlug}>
                <polygon
                  points={points}
                  fill={color}
                  fillOpacity={isSelected ? 0.25 : 0.08}
                  stroke={color}
                  strokeWidth={selectedPersona === summary.personaSlug ? 2.5 : 1.5}
                />
                {dimensions.map((dim, dIdx) => {
                  const pt = getCoordinates(values[dIdx], dim.angle);
                  return (
                    <circle
                      key={dIdx}
                      cx={pt.x}
                      cy={pt.y}
                      r={3.5}
                      fill={color}
                      className="transition-transform hover:scale-150"
                    />
                  );
                })}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Persona Score Breakdown Cards */}
      <div className="flex-1 w-full space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Persona Score Breakdown</span>
          <span className="text-xs text-blue-400 font-medium">Decomposed G-Eval</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {summaries.map((summary, idx) => {
            const isSelected = selectedPersona === summary.personaSlug;
            const color = colors[idx % colors.length];

            return (
              <button
                key={summary.personaSlug}
                onClick={() => onSelectPersona?.(summary.personaSlug)}
                className={`p-3 rounded-lg border text-left transition-all ${
                  isSelected
                    ? 'bg-slate-800 border-blue-500 shadow-md ring-1 ring-blue-500/50'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-xs font-semibold text-slate-200">{summary.personaName}</span>
                  </div>
                  <span className="text-xs font-bold text-emerald-400">{summary.avgCompositeScore} / 100</span>
                </div>

                <div className="grid grid-cols-4 gap-1 text-[10px] text-slate-400 pt-1 border-t border-slate-800/80">
                  <div>Goal: <span className="text-slate-200 font-medium">{summary.avgGoalCompletion}%</span></div>
                  <div>Tool: <span className="text-slate-200 font-medium">{summary.avgToolPrecision}%</span></div>
                  <div>AST: <span className="text-emerald-400 font-medium">{summary.avgSafetyCompliance}%</span></div>
                  <div>Lat: <span className="text-slate-200 font-medium">{summary.avgLatencyMs}ms</span></div>
                </div>
              </button>
            );
          })}
        </div>

        {activeSummary && (
          <div className="mt-3 p-3 bg-slate-950/80 border border-slate-800 rounded-lg text-xs text-slate-300">
            <span className="font-semibold text-blue-400">{activeSummary.personaName} Benchmark Health:</span>{' '}
            {activeSummary.avgCompositeScore >= 85
              ? 'Excellent performance across all dimensions. Ready for enterprise production.'
              : 'Passable; tool precision or safety calibration recommended in active flywheel queue.'}
          </div>
        )}
      </div>
    </div>
  );
};
