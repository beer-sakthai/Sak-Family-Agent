/**
 * The dashboard's sections, defined once.
 *
 * The sidebar, the topbar heading, the command palette and the keyboard
 * shortcuts all read this list. Previously the tab list lived inline in
 * `page.tsx`, which is fine for one consumer and a drift hazard for four.
 */

import {
  Activity,
  BarChart3,
  Database,
  GitBranch,
  MessageSquare,
  Shield,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

export type TabId =
  | "overview"
  | "analytics"
  | "sessions"
  | "memory"
  | "workflows"
  | "audit"
  | "stitch";

export interface NavItem {
  id: TabId;
  label: string;
  /** Shown under the title in the topbar and as the palette's second line. */
  description: string;
  icon: LucideIcon;
  /** Tailwind classes for the item's accent when it is the active section. */
  accent: string;
}

export const NAV_ITEMS: readonly NavItem[] = [
  {
    id: "overview",
    label: "Overview",
    description: "Per-persona activity, memory shards, and configured models",
    icon: Activity,
    accent: "text-hue-cyan",
  },
  {
    id: "analytics",
    label: "Analytics",
    description: "Token distribution, latency trends, and execution outcomes",
    icon: BarChart3,
    accent: "text-hue-violet",
  },
  {
    id: "sessions",
    label: "Sessions",
    description: "Recorded agent runs and their full transcripts",
    icon: MessageSquare,
    accent: "text-hue-sky",
  },
  {
    id: "memory",
    label: "Memory",
    description: "Facts and observations merged across every persona's shard",
    icon: Database,
    accent: "text-hue-emerald",
  },
  {
    id: "workflows",
    label: "Workflows",
    description: "agent_workflow runs, step by step",
    icon: GitBranch,
    accent: "text-hue-amber",
  },
  {
    id: "audit",
    label: "Audit",
    description: "Security events recorded by the guardrail policy",
    icon: Shield,
    accent: "text-hue-rose",
  },
  {
    id: "stitch",
    label: "Stitch",
    description: "Design-system showcase — reads no runtime data",
    icon: Sparkles,
    accent: "text-hue-fuchsia",
  },
] as const;

const TAB_IDS = new Set<string>(NAV_ITEMS.map((item) => item.id));

/** Narrow an untrusted string (a URL fragment, a stored value) to a TabId. */
export function isTabId(value: string | null | undefined): value is TabId {
  return typeof value === "string" && TAB_IDS.has(value);
}

export function navItem(id: TabId): NavItem {
  // Non-null: `id` is a TabId, and NAV_ITEMS covers the union exhaustively.
  return NAV_ITEMS.find((item) => item.id === id)!;
}
