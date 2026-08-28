"use client";

import React from "react";
import { Download, Link2, Maximize2, Menu, Minimize2, RefreshCw, Search } from "lucide-react";

import DemoModeToggle from "@/components/DemoModeToggle";
import DisplayMenu from "@/components/DisplayMenu";
import PersonaFilter from "@/components/PersonaFilter";
import type { DataSource } from "@/lib/contracts.generated";
import { relativeTime } from "@/lib/format";
import { navItem, type TabId } from "@/lib/nav";
import type { Density, Theme } from "@/lib/theme";

/** Auto-refresh choices, in seconds. `0` is off. */
export const REFRESH_INTERVALS = [0, 15, 30, 60] as const;
export type RefreshInterval = (typeof REFRESH_INTERVALS)[number];

interface TopBarProps {
  active: TabId;
  isDemo: boolean;
  onDemoToggle: (next: boolean) => void;
  activeSource: DataSource | null;
  isLoading: boolean;
  onRefresh: () => void;
  refreshInterval: RefreshInterval;
  onRefreshIntervalChange: (seconds: RefreshInterval) => void;
  /** Epoch ms of the last completed refresh, or null before the first one. */
  lastUpdatedAt: number | null;
  /** Ticks so the "x ago" label ages without a re-fetch. */
  now: number;
  onOpenPalette: () => void;
  onOpenMobileNav: () => void;
  theme: Theme;
  onThemeChange: (next: Theme) => void;
  density: Density;
  onDensityChange: (next: Density) => void;
  prefersLight: boolean;
  /** Persona filter selection; empty means the whole family. */
  personas: string[];
  onPersonasChange: (next: string[]) => void;
  /** Run counts per persona, shown beside each name in the filter menu. */
  personaCounts?: Record<string, number>;
  /** False when the active panel holds no rows — the button says so. */
  canExport: boolean;
  onExport: (format: "json" | "csv") => void;
  onCopyLink: () => void;
  /** Presentation mode hides the chrome for a wall-mounted display. */
  presenting: boolean;
  onPresentingChange: (next: boolean) => void;
}

function intervalLabel(seconds: RefreshInterval): string {
  return seconds === 0 ? "Off" : `${seconds}s`;
}

export function TopBar({
  active,
  isDemo,
  onDemoToggle,
  activeSource,
  isLoading,
  onRefresh,
  refreshInterval,
  onRefreshIntervalChange,
  lastUpdatedAt,
  now,
  onOpenPalette,
  onOpenMobileNav,
  theme,
  onThemeChange,
  density,
  onDensityChange,
  prefersLight,
  personas,
  onPersonasChange,
  personaCounts,
  canExport,
  onExport,
  onCopyLink,
  presenting,
  onPresentingChange,
}: TopBarProps) {
  const item = navItem(active);

  return (
    <header className="sticky top-0 z-40 border-b border-line/70 bg-canvas/85 backdrop-blur-xl">
      <div className="flex flex-wrap items-center gap-3 px-4 py-3 sm:px-6">
        <button
          onClick={onOpenMobileNav}
          aria-label="Open navigation menu"
          className="rounded-xl border border-line bg-panel/60 p-2 text-fg-3 transition-colors hover:border-line-strong hover:text-fg focus:outline-none focus-visible:ring-2 focus-visible:ring-accent lg:hidden"
        >
          <Menu className="h-4 w-4" />
        </button>

        <div className="min-w-0 flex-1">
          <h1 className="truncate font-display text-lg font-bold tracking-tight text-fg">
            {item.label}
          </h1>
          <p className="truncate text-xs text-fg-4">{item.description}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* A palette trigger that looks like a search field: the shortcut is
              discoverable without a tour, and it still works on touch. */}
          <button
            onClick={onOpenPalette}
            aria-label="Open command palette"
            data-chrome="secondary"
            className="hidden items-center gap-2 rounded-xl border border-line bg-panel/60 px-3 py-1.5 text-[11px] text-fg-4 transition-colors hover:border-line-strong hover:text-fg-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent sm:flex"
          >
            <Search className="h-3.5 w-3.5" />
            Jump to…
            <kbd className="rounded border border-line-strong bg-sunken px-1.5 py-0.5 font-mono text-[10px] text-fg-3">
              ⌘K
            </kbd>
          </button>

          <span data-chrome="secondary">
            <PersonaFilter
              selected={personas}
              onChange={onPersonasChange}
              counts={personaCounts}
            />
          </span>

          <DemoModeToggle isDemo={isDemo} onToggle={onDemoToggle} activeSource={activeSource} />

          <DisplayMenu
            theme={theme}
            onThemeChange={onThemeChange}
            density={density}
            onDensityChange={onDensityChange}
            prefersLight={prefersLight}
          />

          <label
            data-chrome="secondary"
            className="inline-flex items-center gap-1.5 rounded-xl border border-line bg-panel/60 px-2.5 py-1.5 font-mono text-[11px] text-fg-3 focus-within:ring-2 focus-within:ring-hue-cyan"
          >
            <span className="text-fg-4">Auto</span>
            <select
              aria-label="Auto-refresh interval"
              value={refreshInterval}
              onChange={(event) =>
                onRefreshIntervalChange(Number(event.target.value) as RefreshInterval)
              }
              className="bg-transparent text-fg outline-none"
            >
              {REFRESH_INTERVALS.map((seconds) => (
                <option key={seconds} value={seconds} className="bg-panel">
                  {intervalLabel(seconds)}
                </option>
              ))}
            </select>
          </label>

          <button
            onClick={onCopyLink}
            data-chrome="secondary"
            aria-label="Copy a link to this view"
            title="Copy a link to this view"
            className="hidden rounded-xl border border-line bg-panel/60 p-2 text-fg-3 transition-colors hover:border-line-strong hover:text-fg-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent sm:block"
          >
            <Link2 className="h-3.5 w-3.5" />
          </button>

          {/* A select rather than two buttons: export is a rare action, and
              two more buttons in this row would crowd the ones used often. */}
          <label
            data-chrome="secondary"
            className="inline-flex items-center gap-1.5 rounded-xl border border-line bg-panel/60 px-2.5 py-1.5 font-mono text-[11px] text-fg-3 focus-within:ring-2 focus-within:ring-accent"
          >
            <Download className="h-3 w-3" aria-hidden />
            <select
              aria-label="Export the current panel"
              value=""
              disabled={!canExport}
              onChange={(event) => {
                const format = event.target.value;
                if (format === "json" || format === "csv") onExport(format);
                // Back to the placeholder, so exporting the same format twice
                // in a row still fires a change event.
                event.target.value = "";
              }}
              className="bg-transparent text-fg-2 outline-none disabled:opacity-50"
            >
              <option value="" className="bg-panel">
                {canExport ? "Export" : "No rows"}
              </option>
              <option value="json" className="bg-panel">
                JSON
              </option>
              <option value="csv" className="bg-panel">
                CSV
              </option>
            </select>
          </label>

          <button
            onClick={() => {
              const next = !presenting;
              onPresentingChange(next);
              try {
                if (next) void document.documentElement.requestFullscreen?.();
                else if (document.fullscreenElement) void document.exitFullscreen?.();
              } catch {
                // Fullscreen is gesture- and permission-gated, and absent in
                // some embeddings. The mode still applies without it.
              }
            }}
            aria-pressed={presenting}
            aria-label="Toggle presentation mode"
            title={presenting ? "Leave presentation mode" : "Presentation mode"}
            className="rounded-xl border border-line bg-panel/60 p-2 text-fg-3 transition-colors hover:border-line-strong hover:text-fg-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            {presenting ? (
              <Minimize2 className="h-3.5 w-3.5" />
            ) : (
              <Maximize2 className="h-3.5 w-3.5" />
            )}
          </button>

          <button
            onClick={onRefresh}
            disabled={isLoading}
            aria-label="Refresh dashboard data"
            className="inline-flex items-center gap-1.5 rounded-xl border border-line bg-panel/60 px-3 py-1.5 font-mono text-[11px] text-fg-2 transition-colors hover:border-line-strong disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <RefreshCw className={`h-3 w-3 ${isLoading ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">
              {lastUpdatedAt === null ? "Refresh" : relativeTime(lastUpdatedAt, now)}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}

export default TopBar;
