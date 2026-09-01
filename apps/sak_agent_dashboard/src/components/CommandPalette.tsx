"use client";

import React, { useMemo, useState } from "react";
import { CornerDownLeft, Search, X } from "lucide-react";

import { useFocusTrap } from "@/lib/focus";
import { highlightSegments, rankBy, type FuzzyMatch } from "@/lib/fuzzy";
import { NAV_ITEMS, type TabId } from "@/lib/nav";

export interface Command {
  id: string;
  label: string;
  hint: string;
  group: string;
  run: () => void;
  /** Rendered on the right of the row — the same key that runs it from the page. */
  shortcut?: string;
}

interface Result {
  command: Command;
  /** Where the query matched the label, when it did. */
  match: FuzzyMatch | null;
  /** Whether this row opens a new group, and so carries its heading. */
  startsGroup: boolean;
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
 * Matching is a scored fuzzy subsequence over the label and the description
 * (`lib/fuzzy.ts`), not a substring: "usd" finds "Use sample data" and "ovw"
 * finds "Overview", which is how people actually type into one of these. The
 * matched characters are underlined in the row, so a non-obvious hit explains
 * itself instead of looking like a bug. It is forty lines and no dependency —
 * the note this replaces weighed a dependency it turned out not to need.
 *
 * The caller mounts this only while the palette is open, so the query and the
 * highlighted row reset by unmounting rather than by an effect that clears
 * them — no cascading render, and nothing to keep in sync.
 */
export function CommandPalette({ onClose, onNavigate, actions }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [highlight, setHighlight] = useState(0);
  // The drawer has trapped and returned focus since it landed; the palette,
  // the other modal on this page, did neither.
  const dialogRef = useFocusTrap<HTMLDivElement>();

  const commands = useMemo<Command[]>(
    () => [
      ...NAV_ITEMS.map((item, index) => ({
        id: `nav-${item.id}`,
        label: item.label,
        hint: item.description,
        group: "Go to",
        // The digit that reaches this section from the page, shown on the row
        // it runs rather than only in the shortcuts overlay.
        shortcut: String(index + 1),
        run: () => onNavigate(item.id),
      })),
      ...actions,
    ],
    [onNavigate, actions],
  );

  // An empty query keeps the declared order — sections, then actions — rather
  // than an arbitrary ranking of identical scores.
  const results = useMemo<Result[]>(() => {
    const matched: { command: Command; match: FuzzyMatch | null }[] =
      query.trim() === ""
        ? commands.map((command) => ({ command, match: null }))
        : rankBy(commands, query, (command) => [command.label, command.hint]).map((ranked) => ({
            command: ranked.item,
            // Only highlight when the label itself matched; underlining half
            // the description because the *hint* matched is noise.
            match: ranked.fieldIndex === 0 ? ranked.match : null,
          }));

    // The group heading belongs to the first row of each run. Computed here
    // rather than by mutating a variable inside the render's `map`, so the
    // list renders the same whether React renders it once or twice.
    return matched.map((entry, index) => ({
      ...entry,
      startsGroup: entry.command.group !== matched[index - 1]?.command.group,
    }));
  }, [commands, query]);

  const clampedHighlight = results.length === 0 ? 0 : Math.min(highlight, results.length - 1);

  const runAt = (index: number) => {
    const result = results[index];
    if (!result) return;
    result.command.run();
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

  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center p-4 pt-[12vh]">
      <button
        aria-label="Close command palette"
        onClick={onClose}
        className="absolute inset-0 h-full w-full bg-sunken/80 backdrop-blur-sm"
      />
      <div
        ref={dialogRef}
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
          {query && (
            <button
              type="button"
              aria-label="Clear search query"
              title="Clear search query"
              onClick={() => {
                setQuery("");
                setHighlight(0);
              }}
              className="rounded-lg p-1 text-fg-4 transition-colors hover:bg-raised/80 hover:text-fg focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <X className="h-3.5 w-3.5" aria-hidden />
            </button>
          )}
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
          {results.map(({ command, match, startsGroup }, index) => {
            const segments = highlightSegments(command.label, match?.positions ?? []);
            return (
              <React.Fragment key={command.id}>
                {startsGroup && (
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
                      <span className="block truncate text-sm font-medium">
                        {segments.map((segment, segmentIndex) =>
                          segment.matched ? (
                            <mark
                              key={segmentIndex}
                              className="bg-transparent text-accent underline decoration-accent/60 underline-offset-2"
                            >
                              {segment.text}
                            </mark>
                          ) : (
                            <React.Fragment key={segmentIndex}>{segment.text}</React.Fragment>
                          ),
                        )}
                      </span>
                      <span className="block truncate text-[11px] text-fg-4">
                        {command.hint}
                      </span>
                    </span>
                    {command.shortcut && (
                      <kbd className="hidden shrink-0 rounded border border-line-strong bg-sunken px-1.5 py-0.5 font-mono text-[10px] text-fg-4 sm:block">
                        {command.shortcut}
                      </kbd>
                    )}
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
