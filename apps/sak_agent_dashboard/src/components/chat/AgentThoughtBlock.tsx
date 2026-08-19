'use client';

import React, { useState } from 'react';

interface AgentThoughtBlockProps {
  persona: string;
  thought: string;
  isStreaming?: boolean;
}

const PERSONA_COLORS: Record<string, string> = {
  sakthai: 'border-blue-500/30 bg-blue-950/20 text-blue-300',
  sakking: 'border-amber-500/30 bg-amber-950/20 text-amber-300',
  saksee: 'border-purple-500/30 bg-purple-950/20 text-purple-300',
  sakjules: 'border-emerald-500/30 bg-emerald-950/20 text-emerald-300',
  saksit: 'border-cyan-500/30 bg-cyan-950/20 text-cyan-300',
  saktan: 'border-rose-500/30 bg-rose-950/20 text-rose-300',
};

export const AgentThoughtBlock: React.FC<AgentThoughtBlockProps> = ({
  persona,
  thought,
  isStreaming = false,
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const colorClass = PERSONA_COLORS[persona.toLowerCase()] || 'border-slate-700 bg-slate-900/40 text-slate-300';
  const personaName = persona.charAt(0).toUpperCase() + persona.slice(1);

  return (
    <div className={`my-2 rounded-lg border ${colorClass} p-3 text-xs transition-all`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-label={`Toggle ${personaName}'s reasoning process`}
        className="flex w-full items-center justify-between font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-purple-400 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-950 rounded"
      >
        <span className="flex items-center gap-2">
          <span>🧠</span>
          <span>{personaName}&apos;s Reasoning Process</span>
          {isStreaming && <span className="animate-pulse text-amber-400">● Thinking...</span>}
        </span>
        <span className="text-slate-400">{isOpen ? '▲ Collapse' : '▼ Expand'}</span>
      </button>

      {isOpen && (
        <div className="mt-2 whitespace-pre-wrap font-mono text-[11px] leading-relaxed opacity-90">
          {thought}
        </div>
      )}
    </div>
  );
};
