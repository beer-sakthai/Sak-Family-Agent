'use client';

import React, { useState } from 'react';
import { PersonaSelector } from './PersonaSelector';
import { AgentThoughtBlock } from './AgentThoughtBlock';
import { ToolExecutionCard } from './ToolExecutionCard';
import { SynthesisCard } from './SynthesisCard';
import { PersonaPresetId, SSEChatEvent, SupervisorPlan } from '../../lib/types';

export const ChatStudio: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [activePersonas, setActivePersonas] = useState<string[]>(['sakthai', 'sakking', 'sakjules']);
  const [selectedPreset, setSelectedPreset] = useState<PersonaPresetId>('cloud_powerhouse');
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState('session_idle');
  const [plan, setPlan] = useState<SupervisorPlan | null>(null);
  const [thoughts, setThoughts] = useState<Array<{ persona: string; thought: string }>>([]);
  const [tools, setTools] = useState<
    Array<{
      callId: string;
      persona: string;
      tool: string;
      args: Record<string, unknown>;
      output?: string;
      astSafe?: boolean;
    }>
  >([]);
  const [synthesis, setSynthesis] = useState('');
  const [stagedStatus, setStagedStatus] = useState(false);

  const togglePersona = (personaId: string) => {
    setActivePersonas((prev) =>
      prev.includes(personaId) ? prev.filter((p) => p !== personaId) : [...prev, personaId]
    );
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isStreaming) return;

    setIsStreaming(true);
    setThoughts([]);
    setTools([]);
    setSynthesis('');
    setPlan(null);
    setStagedStatus(false);

    try {
      const response = await fetch('/api/chatkit/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          personas: activePersonas,
          preset: selectedPreset,
        }),
      });

      if (!response.body) {
        throw new Error('No stream body received');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event: SSEChatEvent = JSON.parse(line.slice(6));
              switch (event.type) {
                case 'session_start':
                  setSessionId(event.sessionId);
                  break;
                case 'supervisor_plan':
                  setPlan(event.plan);
                  break;
                case 'persona_thought':
                  setThoughts((prev) => [...prev, { persona: event.persona, thought: event.chunk }]);
                  break;
                case 'tool_call':
                  setTools((prev) => [
                    ...prev,
                    {
                      callId: event.callId,
                      persona: event.persona,
                      tool: event.tool,
                      args: event.args,
                    },
                  ]);
                  break;
                case 'tool_output':
                  setTools((prev) =>
                    prev.map((t) =>
                      t.callId === event.callId
                        ? { ...t, output: event.output, astSafe: event.astSafe }
                        : t
                    )
                  );
                  break;
                case 'synthesis_chunk':
                  setSynthesis((prev) => prev + event.chunk);
                  break;
                case 'staged_dataset_entry':
                  setStagedStatus(true);
                  break;
                case 'session_complete':
                  setIsStreaming(false);
                  break;
              }
            } catch {
              // Ignore partial JSON
            }
          }
        }
      }
    } catch (err) {
      console.error('Chat dispatch stream error:', err);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Top: Persona & Preset Matrix */}
      <PersonaSelector
        selectedPreset={selectedPreset}
        activePersonas={activePersonas}
        onSelectPreset={setSelectedPreset}
        onTogglePersona={togglePersona}
      />

      {/* Main Studio Arena */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 backdrop-blur">
        {/* Supervisor Plan Card */}
        {plan && (
          <div className="mb-4 rounded-lg border border-blue-500/30 bg-blue-950/20 p-3 text-xs">
            <div className="flex items-center gap-2 font-semibold text-blue-300">
              <span>👑</span>
              <span>Supervisor Plan Decomposition</span>
            </div>
            <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
              {plan.subtasks.map((task) => (
                <div key={task.id} className="rounded border border-slate-800 bg-slate-950/50 p-2">
                  <div className="font-semibold text-slate-300 capitalize">{task.persona} Subtask</div>
                  <div className="text-[11px] text-slate-400">{task.goal}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Thought Blocks Stream */}
        {thoughts.map((item, idx) => (
          <AgentThoughtBlock
            key={idx}
            persona={item.persona}
            thought={item.thought}
            isStreaming={isStreaming && idx === thoughts.length - 1}
          />
        ))}

        {/* Interactive Tool Execution Cards */}
        {tools.map((item) => (
          <ToolExecutionCard
            key={item.callId}
            persona={item.persona}
            tool={item.tool}
            args={item.args}
            output={item.output}
            astSafe={item.astSafe}
          />
        ))}

        {/* Synthesis Result */}
        {synthesis && (
          <SynthesisCard
            content={synthesis}
            sessionId={sessionId}
            isStreaming={isStreaming}
            stagedStatus={stagedStatus}
          />
        )}

        {/* Empty state */}
        {!plan && thoughts.length === 0 && !synthesis && (
          <div className="py-12 text-center text-slate-500 text-xs">
            <div className="text-3xl mb-2">⚔️</div>
            <p>Collaborative Arena is ready. Select personas, choose a preset, and dispatch a challenge!</p>
          </div>
        )}

        {/* Prompt Input Form */}
        <form onSubmit={handleSend} className="mt-4 flex gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="E.g., Review security guardrails, verify AST sandbox, and prepare automated CI/CD..."
            aria-label="Dispatch prompt"
            disabled={isStreaming}
            className="flex-1 rounded-lg border border-slate-800 bg-slate-950 px-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
          />
          <button
            type="submit"
            disabled={isStreaming || !prompt.trim()}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white shadow hover:bg-blue-500 disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
          >
            {isStreaming ? 'Streaming...' : '🚀 Dispatch'}
          </button>
        </form>
      </div>
    </div>
  );
};
