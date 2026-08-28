"use client";

import React, { useMemo, useState } from "react";
import { CornerDownLeft, Search } from "lucide-react";

import { NAV_ITEMS, type TabId } from "@/lib/nav";

export interface Command {
  id: string;
  label: string;
  hint: string;
  group: string;
  run: () => void;
}

interface CommandPaletteProps {
  onClose: () => void;
  onNavigate: (tab: TabId) => void;
  /** Actions beyond navigation — refresh, sample data, auto-refresh. */
  actions: Command[];
}

/**
 * ⌘K navigation.
 *
 * Filtering is a plain substring match over label and hint. Fuzzy ranking
 * would be a dependency and a behaviour to explain for a list of at most a
 * dozen entries.
 *
 * The caller mounts this only while the palette is open, so the query and the
 * highlighted row reset by unmounting rather than by an effect that clears
 * them — no cascading render, and nothing to keep in sync.
 */
export function CommandPalette({ onClose, onNavigate, actions }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [highlight, setHighlight] = useState(0);

  const commands = useMemo<Command[]>(
    () => [
      ...NAV_ITEMS.map((item) => ({
        id: `nav-${item.id}`,
        label: item.label,
        hint: item.description,
        group: "Go to",
        run: () => onNavigate(item.id),
      })),
      ...actions,
    ],
    [onNavigate, actions],
  );

  const results = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return commands;
    return commands.filter(
      (command) =>
        command.label.toLowerCase().includes(needle) ||
        command.hint.toLowerCase().includes(needle),
    );
  }, [commands, query]);

  const clampedHighlight = results.length === 0 ? 0 : Math.min(highlight, results.length - 1);

  const runAt = (index: number) => {
    const command = results[index];
    if (!command) return;
    command.run();
    onClose();
  };

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlight((current) => (results.length === 0 ? 0 : (current + 1) % results.length));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlight((current) =>
        results.length === 0 ? 0 : (current - 1 + results.length) % results.length,
      );
    } else if (event.key === "Enter") {
      event.preventDefault();
      runAt(clampedHighlight);
    } else if (event.key === "Escape") {
      event.preventDefault();
      onClose();
    }
  };

  let lastGroup = "";

  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center p-4 pt-[12vh]">
      <button
        aria-label="Close command palette"
        onClick={onClose}
        className="absolute inset-0 h-full w-full bg-sunken/80 backdrop-blur-sm"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        onKeyDown={onKeyDown}
        className="relative w-full max-w-lg overflow-hidden rounded-2xl border border-line-strong/70 bg-panel/95 shadow-2xl shadow-black/60"
      >
        <div className="flex items-center gap-2 border-b border-line px-4 py-3">
          <Search className="h-4 w-4 shrink-0 text-fg-4" aria-hidden />
          <input
            // The palette is a modal opened by an explicit ⌘K; focusing its
            // only field is the whole point of opening it.
            autoFocus
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setHighlight(0);
            }}
            placeholder="Jump to a section or run a command…"
            aria-label="Search commands"
            className="w-full bg-transparent text-sm text-fg placeholder:text-fg-5 outline-none"
          />
          <kbd className="hidden rounded border border-line-strong bg-sunken px-1.5 py-0.5 font-mono text-[10px] text-fg-4 sm:block">
            esc
          </kbd>
        </div>

        <ul className="max-h-[50vh] overflow-y-auto p-2" role="listbox" aria-label="Commands">
          {results.length === 0 && (
            <li className="px-3 py-6 text-center font-mono text-xs text-fg-4">
              Nothing matches “{query}”.
            </li>
          )}
          {results.map((command, index) => {
            const showGroup = command.group !== lastGroup;
            lastGroup = command.group;
            return (
              <React.Fragment key={command.id}>
                {showGroup && (
                  <li
                    aria-hidden
                    className="px-3 pb-1 pt-3 text-[10px] font-medium uppercase tracking-wider text-fg-5"
                  >
                    {command.group}
                  </li>
                )}
                <li>
                  <button
                    role="option"
                    aria-selected={index === clampedHighlight}
                    onMouseEnter={() => setHighlight(index)}
                    onClick={() => runAt(index)}
                    className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                      index === clampedHighlight
                        ? "bg-raised/80 text-fg"
                        : "text-fg-2 hover:bg-raised/40"
                    }`}
                  >
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium">{command.label}</span>
                      <span className="block truncate text-[11px] text-fg-4">
                        {command.hint}
                      </span>
                    </span>
                    {index === clampedHighlight && (
                      <CornerDownLeft className="h-3.5 w-3.5 shrink-0 text-fg-4" aria-hidden />
                    )}
                  </button>
                </li>
              </React.Fragment>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

export default CommandPalette;
