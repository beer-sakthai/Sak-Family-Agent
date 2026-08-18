'use client';

import React from 'react';
import { PersonaPreset, PersonaPresetId } from '../../lib/types';
import { PERSONA_PRESETS } from '../../lib/orchestrator/supervisor';

interface PersonaSelectorProps {
  selectedPreset: PersonaPresetId;
  activePersonas: string[];
  onSelectPreset: (presetId: PersonaPresetId) => void;
  onTogglePersona: (personaId: string) => void;
}

const PERSONA_ROSTER = [
  { id: 'sakthai', name: 'SakThai', role: 'Master Orchestrator', icon: '👑', color: 'text-blue-400' },
  { id: 'sakking', name: 'SakKing', role: 'Security & AST Guardrails', icon: '🛡️', color: 'text-amber-400' },
  { id: 'saksee', name: 'SakSee', role: 'Multimodal & Visual UI', icon: '🎨', color: 'text-purple-400' },
  { id: 'sakjules', name: 'SakJules', role: 'CI/CD & Automation Master', icon: '⚡', color: 'text-emerald-400' },
  { id: 'saksit', name: 'SakSit', role: 'Content & API Contracts', icon: '✍️', color: 'text-cyan-400' },
  { id: 'saktan', name: 'SakTan', role: 'Daily Ops & Local Sandbox', icon: '🔧', color: 'text-rose-400' },
];

export const PersonaSelector: React.FC<PersonaSelectorProps> = ({
  selectedPreset,
  activePersonas,
  onSelectPreset,
  onTogglePersona,
}) => {
  const currentPreset = PERSONA_PRESETS.find((p) => p.id === selectedPreset) || PERSONA_PRESETS[0];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Team Preset &amp; Persona Matrix</h3>
          <p className="text-xs text-slate-400">{currentPreset.description}</p>
        </div>
        <div className="flex gap-1.5">
          {PERSONA_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => onSelectPreset(preset.id)}
              className={`flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
                selectedPreset === preset.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              <span>{preset.icon}</span>
              <span>{preset.name}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-6">
        {PERSONA_ROSTER.map((persona) => {
          const isActive = activePersonas.includes(persona.id);
          const mapping = currentPreset.personaMappings[persona.id];

          return (
            <div
              key={persona.id}
              onClick={() => onTogglePersona(persona.id)}
              className={`cursor-pointer rounded-lg border p-2.5 transition-all select-none ${
                isActive
                  ? 'border-blue-500/50 bg-blue-950/20 text-slate-100 shadow-sm'
                  : 'border-slate-800 bg-slate-950/40 text-slate-500 opacity-60 hover:opacity-100'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-base">{persona.icon}</span>
                <span
                  className={`h-2 w-2 rounded-full ${
                    isActive ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-slate-600'
                  }`}
                />
              </div>
              <div className={`mt-1 font-semibold text-xs ${persona.color}`}>{persona.name}</div>
              <div className="text-[10px] text-slate-400 truncate">{persona.role}</div>
              {mapping && (
                <div className="mt-1.5 rounded bg-slate-900/80 px-1 py-0.5 text-[9px] text-slate-400 truncate">
                  {mapping.provider}: {mapping.model}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
