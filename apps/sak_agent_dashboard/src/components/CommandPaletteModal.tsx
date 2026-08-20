'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Search,
  Radio,
  Dna,
  ShieldAlert,
  Zap,
  Target,
  Telescope,
  Activity,
  Layers,
  ArrowRight,
  X,
} from 'lucide-react';

interface CommandPaletteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (tabId: string) => void;
}

export const CommandPaletteModal: React.FC<CommandPaletteModalProps> = ({
  isOpen,
  onClose,
  onNavigate,
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [prevIsOpen, setPrevIsOpen] = useState(isOpen);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Sync state when opening the modal without triggering effect setState warnings
  if (isOpen !== prevIsOpen) {
    setPrevIsOpen(isOpen);
    if (isOpen) {
      setSelectedIndex(0);
    }
  }

  const commandItems = [
    {
      id: 'war_room',
      title: 'Agent War Room & Mesh Visualizer',
      subtitle: 'Live SVG dynamic bezier links and node telemetry dials',
      icon: Activity,
      category: 'Operations',
    },
    {
      id: 'red_team',
      title: 'Autonomous Red Team Fuzzer',
      subtitle: 'Multi-turn prompt injection & AST evasion fuzzing engine',
      icon: ShieldAlert,
      category: 'Security',
    },
    {
      id: 'mutation_studio',
      title: 'Mutation Testing & Auto-Healer Studio',
      subtitle: 'Fault injection, kill scores, and synthesized unit tests',
      icon: Dna,
      category: 'CI/CD & Quality',
    },
    {
      id: 'semantic_cache',
      title: 'Semantic Cache & Token Cost Optimizer',
      subtitle: '64-D L2 cosine similarity response cache ($0.00 cost)',
      icon: Zap,
      category: 'Optimization',
    },
    {
      id: 'a2a_registry',
      title: 'A2A Interoperability & Service Registry',
      subtitle: 'JSON-RPC 2.0 multi-agent delegation & fleet discovery',
      icon: Layers,
      category: 'Orchestration',
    },
    {
      id: 'eval_flywheel',
      title: 'Quality Flywheel & G-Eval Benchmark',
      subtitle: 'Multi-turn trajectory scoring & golden benchmark suites',
      icon: Target,
      category: 'Evaluation',
    },
    {
      id: 'adk_bridge',
      title: 'Google ADK & Cloud Trace Observability',
      subtitle: 'Distributed OpenTelemetry waterfall & BigQuery analytics',
      icon: Telescope,
      category: 'Cloud & Telemetry',
    },
    {
      id: 'telegram_hub',
      title: 'Telegram Voice Bridge & Duplex Audio',
      subtitle: 'Gemini 2.0 Multimodal live voice streaming & emergency alerts',
      icon: Radio,
      category: 'Voice & Mobile',
    },
  ];

  const filteredItems = commandItems.filter(
    (item) =>
      item.title.toLowerCase().includes(query.toLowerCase()) ||
      item.subtitle.toLowerCase().includes(query.toLowerCase()) ||
      item.category.toLowerCase().includes(query.toLowerCase())
  );

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setSelectedIndex(0);
  };

  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => inputRef.current?.focus(), 50);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  const handleSelect = useCallback(
    (tabId: string) => {
      setQuery('');
      onNavigate(tabId);
      onClose();
    },
    [onNavigate, onClose]
  );

  // Keyboard navigation for ArrowUp, ArrowDown, Enter, Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        setQuery('');
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) =>
          filteredItems.length > 0 ? (prev + 1) % filteredItems.length : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) =>
          filteredItems.length > 0
            ? (prev - 1 + filteredItems.length) % filteredItems.length
            : 0
        );
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredItems[selectedIndex]) {
          handleSelect(filteredItems[selectedIndex].id);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredItems, selectedIndex, onClose, handleSelect]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Command Palette"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          setQuery('');
          onClose();
        }
      }}
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-black/70 backdrop-blur-sm animate-fade-in"
    >
      <div className="w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Search Header */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-800 bg-slate-950/60">
          <Search className="w-5 h-5 text-slate-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleQueryChange}
            placeholder="Type a command or jump to studio panel (e.g. 'Red Team', 'Mutation', 'Cache')..."
            className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
            aria-label="Search studio panels or commands"
          />
          <button
            onClick={onClose}
            aria-label="Close command palette"
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div
          role="listbox"
          aria-label="Command options"
          className="max-h-80 overflow-y-auto p-2 space-y-1"
        >
          {filteredItems.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500">
              No matching commands or studio panels found.
            </div>
          ) : (
            filteredItems.map((item, index) => {
              const Icon = item.icon;
              const isSelected = index === selectedIndex;
              return (
                <div
                  key={item.id}
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => handleSelect(item.id)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-colors group ${
                    isSelected
                      ? 'bg-slate-800/80 ring-1 ring-cyan-500/50'
                      : 'hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className={`p-2 rounded-lg bg-slate-950 border transition-colors ${
                        isSelected
                          ? 'border-cyan-500/50 text-cyan-300'
                          : 'border-slate-800 text-cyan-400 group-hover:border-cyan-500/50 group-hover:text-cyan-300'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-slate-200 group-hover:text-white flex items-center gap-2">
                        {item.title}
                        <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-950 text-slate-400 border border-slate-800">
                          {item.category}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 truncate">
                        {item.subtitle}
                      </div>
                    </div>
                  </div>

                  <ArrowRight
                    className={`w-4 h-4 transform transition-all flex-shrink-0 ${
                      isSelected
                        ? 'text-cyan-400 translate-x-0.5'
                        : 'text-slate-600 group-hover:text-cyan-400 group-hover:translate-x-0.5'
                    }`}
                  />
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 bg-slate-950 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span>
              Navigate:{' '}
              <kbd className="px-1.5 py-0.5 rounded bg-slate-800 font-mono text-[10px] text-slate-300">
                ↑
              </kbd>
              <kbd className="px-1.5 py-0.5 rounded bg-slate-800 font-mono text-[10px] text-slate-300 ml-1">
                ↓
              </kbd>
            </span>
            <span>
              Select:{' '}
              <kbd className="px-1.5 py-0.5 rounded bg-slate-800 font-mono text-[10px] text-slate-300">
                Enter
              </kbd>
            </span>
            <span>
              Close:{' '}
              <kbd className="px-1.5 py-0.5 rounded bg-slate-800 font-mono text-[10px] text-slate-300">
                Esc
              </kbd>
            </span>
          </div>
          <span className="font-mono text-[10px] text-teal-400 font-semibold">
            Sak-Family Command Palette
          </span>
        </div>
      </div>
    </div>
  );
};
