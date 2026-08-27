"use client";

import React from "react";
import { Menu, RefreshCw, Search } from "lucide-react";

import DemoModeToggle from "@/components/DemoModeToggle";
import type { DataSource } from "@/lib/contracts.generated";
import { relativeTime } from "@/lib/format";
import { navItem, type TabId } from "@/lib/nav";

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
}: TopBarProps) {
  const item = navItem(active);

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800/70 bg-[#070a12]/85 backdrop-blur-xl">
      <div className="flex flex-wrap items-center gap-3 px-4 py-3 sm:px-6">
        <button
          onClick={onOpenMobileNav}
          aria-label="Open navigation menu"
          className="rounded-xl border border-slate-800 bg-slate-900/60 p-2 text-slate-400 transition-colors hover:border-slate-700 hover:text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 lg:hidden"
        >
          <Menu className="h-4 w-4" />
        </button>

        <div className="min-w-0 flex-1">
          <h1 className="truncate font-display text-lg font-bold tracking-tight text-white">
            {item.label}
          </h1>
          <p className="truncate text-xs text-slate-500">{item.description}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* A palette trigger that looks like a search field: the shortcut is
              discoverable without a tour, and it still works on touch. */}
          <button
            onClick={onOpenPalette}
            aria-label="Open command palette"
            className="hidden items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-[11px] text-slate-500 transition-colors hover:border-slate-700 hover:text-slate-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 sm:flex"
          >
            <Search className="h-3.5 w-3.5" />
            Jump to…
            <kbd className="rounded border border-slate-700 bg-slate-950 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">
              ⌘K
            </kbd>
          </button>

          <DemoModeToggle isDemo={isDemo} onToggle={onDemoToggle} activeSource={activeSource} />

          <label className="inline-flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/60 px-2.5 py-1.5 font-mono text-[11px] text-slate-400 focus-within:ring-2 focus-within:ring-cyan-400">
            <span className="text-slate-500">Auto</span>
            <select
              aria-label="Auto-refresh interval"
              value={refreshInterval}
              onChange={(event) =>
                onRefreshIntervalChange(Number(event.target.value) as RefreshInterval)
              }
              className="bg-transparent text-slate-200 outline-none"
            >
              {REFRESH_INTERVALS.map((seconds) => (
                <option key={seconds} value={seconds} className="bg-slate-900">
                  {intervalLabel(seconds)}
                </option>
              ))}
            </select>
          </label>

          <button
            onClick={onRefresh}
            disabled={isLoading}
            aria-label="Refresh dashboard data"
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-1.5 font-mono text-[11px] text-slate-300 transition-colors hover:border-slate-700 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
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
