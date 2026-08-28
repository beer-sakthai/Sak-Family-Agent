"use client";

import React, { useCallback } from "react";
import { ChevronLeft, ChevronRight, Terminal, X } from "lucide-react";

import { useRovingFocus } from "@/lib/focus";
import { NAV_ITEMS, type TabId } from "@/lib/nav";

interface SidebarProps {
  active: TabId;
  onSelect: (tab: TabId) => void;
  collapsed: boolean;
  onCollapsedChange: (collapsed: boolean) => void;
  /** Counts rendered as a badge beside a section, when one is known. */
  counts: Partial<Record<TabId, number>>;
  /** Mobile: the sidebar is an off-canvas drawer rather than a column. */
  mobileOpen: boolean;
  onMobileClose: () => void;
}

function NavButton({
  item,
  index,
  active,
  collapsed,
  count,
  onSelect,
  register,
}: {
  item: (typeof NAV_ITEMS)[number];
  index: number;
  active: boolean;
  collapsed: boolean;
  count: number | undefined;
  onSelect: (tab: TabId) => void;
  register: (index: number) => (element: HTMLElement | null) => void;
}) {
  const Icon = item.icon;
  return (
    <button
      ref={register(index)}
      role="tab"
      aria-selected={active}
      aria-label={item.label}
      // Roving tabindex: the tablist is one tab stop and the arrow keys move
      // within it, per the WAI-ARIA authoring practice. Seven tab stops
      // between the page start and the panel is the alternative.
      tabIndex={active ? 0 : -1}
      title={collapsed ? item.label : undefined}
      onClick={() => onSelect(item.id)}
      className={`group relative w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
        active
          ? "bg-raised/70 text-fg"
          : "text-fg-3 hover:bg-raised/40 hover:text-fg"
      } ${collapsed ? "justify-center px-0" : ""}`}
    >
      {/* The active marker is a rail, not a background wash: it stays legible
          against the translucent panel and reads at a glance when collapsed. */}
      <span
        aria-hidden
        className={`absolute left-0 top-1/2 -translate-y-1/2 h-6 w-[3px] rounded-r-full transition-all ${
          active ? "bg-hue-cyan opacity-100" : "opacity-0"
        }`}
      />
      <Icon className={`h-4 w-4 shrink-0 ${active ? item.accent : ""}`} />
      {!collapsed && (
        <>
          <span className="truncate font-medium">{item.label}</span>
          {count !== undefined && (
            <span className="ml-auto rounded-full border border-line-strong/70 bg-panel/80 px-1.5 py-0.5 font-mono text-[10px] text-fg-3">
              {count}
            </span>
          )}
        </>
      )}
    </button>
  );
}

export function Sidebar({
  active,
  onSelect,
  collapsed,
  onCollapsedChange,
  counts,
  mobileOpen,
  onMobileClose,
}: SidebarProps) {
  const activeIndex = Math.max(
    0,
    NAV_ITEMS.findIndex((item) => item.id === active),
  );

  // One handler for both copies of the list: choosing a section always closes
  // the drawer, which is a no-op for the desktop column.
  const navigate = useCallback(
    (tab: TabId) => {
      onSelect(tab);
      onMobileClose();
    },
    [onSelect, onMobileClose],
  );

  const activateIndex = useCallback(
    (index: number) => {
      const item = NAV_ITEMS[index];
      if (item) navigate(item.id);
    },
    [navigate],
  );

  const { register, onKeyDown } = useRovingFocus(NAV_ITEMS.length, activeIndex, activateIndex);

  const content = (isCollapsed: boolean) => (
    <>
      <div
        className={`flex items-center gap-2.5 px-2 pb-5 ${isCollapsed ? "justify-center" : ""}`}
      >
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-lg shadow-hue-cyan/20">
          <Terminal className="h-[18px] w-[18px] text-fg" aria-hidden />
        </div>
        {!isCollapsed && (
          <div className="min-w-0">
            <p className="truncate font-display text-sm font-bold tracking-tight text-fg">
              Sak-Agent-Family
            </p>
            <p className="truncate text-[11px] text-fg-4">Runtime dashboard</p>
          </div>
        )}
      </div>

      <nav
        role="tablist"
        aria-label="Dashboard sections"
        aria-orientation="vertical"
        onKeyDown={onKeyDown}
        className="flex flex-1 flex-col gap-1"
      >
        {NAV_ITEMS.map((item, index) => (
          <NavButton
            key={item.id}
            index={index}
            item={item}
            active={active === item.id}
            collapsed={isCollapsed}
            count={counts[item.id]}
            onSelect={navigate}
            register={register}
          />
        ))}
      </nav>

      <button
        onClick={() => onCollapsedChange(!collapsed)}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        className="mt-4 hidden w-full items-center justify-center gap-2 rounded-xl border border-line bg-panel/60 px-3 py-2 font-mono text-[11px] text-fg-3 transition-colors hover:border-line-strong hover:text-fg focus:outline-none focus-visible:ring-2 focus-visible:ring-accent lg:flex"
      >
        {collapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
        {!collapsed && "Collapse"}
      </button>
    </>
  );

  return (
    <>
      {/* Desktop column. `lg:` only — below that the drawer below is the nav. */}
      <aside
        data-testid="sidebar"
        data-chrome="sidebar"
        className={`sticky top-0 hidden h-screen shrink-0 flex-col border-r border-line/70 bg-sunken/60 p-4 backdrop-blur-xl transition-[width] duration-200 lg:flex ${
          collapsed ? "w-[76px]" : "w-[248px]"
        }`}
      >
        {content(collapsed)}
      </aside>

      {/* Mobile drawer. Rendered only when open so its buttons are not
          duplicate tab stops behind the page on a phone. */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            aria-label="Close navigation"
            onClick={onMobileClose}
            className="absolute inset-0 h-full w-full bg-sunken/80 backdrop-blur-sm"
          />
          <aside className="absolute left-0 top-0 flex h-full w-[260px] flex-col border-r border-line/70 bg-sunken/95 p-4">
            <button
              onClick={onMobileClose}
              aria-label="Close navigation menu"
              className="absolute right-3 top-3 rounded-lg p-1.5 text-fg-3 hover:bg-raised/60 hover:text-fg focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <X className="h-4 w-4" />
            </button>
            {content(false)}
          </aside>
        </div>
      )}
    </>
  );
}

export default Sidebar;
