/**
 * Shared UI styling tokens, persona palettes, formatters, and stream buffer utilities
 * for sak_agent_dashboard.
 */

import { TelemetryEventType } from "./types";

export interface PersonaTheme {
  slug: string;
  name: string;
  role: string;
  badge: string;
  border: string;
  glow: string;
  accent: string;
}

export const PERSONA_THEMES: Record<string, PersonaTheme> = {
  sakthai: {
    slug: "sakthai",
    name: "SakThai",
    role: "Foundational Lead & Architect",
    badge: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
    border: "border-cyan-500/30",
    glow: "shadow-cyan-950/40",
    accent: "text-cyan-400",
  },
  sakking: {
    slug: "sakking",
    name: "SakKing",
    role: "Deep Research & Reasoning",
    badge: "bg-purple-500/10 text-purple-400 border-purple-500/30",
    border: "border-purple-500/30",
    glow: "shadow-purple-950/40",
    accent: "text-purple-400",
  },
  saksee: {
    slug: "saksee",
    name: "SakSee",
    role: "UI/UX & Vision Craft",
    badge: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    border: "border-amber-500/30",
    glow: "shadow-amber-950/40",
    accent: "text-amber-400",
  },
  saksit: {
    slug: "saksit",
    name: "SakSit",
    role: "Knowledge Graph & Memory",
    badge: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    border: "border-blue-500/30",
    glow: "shadow-blue-950/40",
    accent: "text-blue-400",
  },
  sakjules: {
    slug: "sakjules",
    name: "SakJules",
    role: "Automation & CI/CD Master",
    badge: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    border: "border-rose-500/30",
    glow: "shadow-rose-950/40",
    accent: "text-rose-400",
  },
  saktan: {
    slug: "saktan",
    name: "SakTan",
    role: "Security Sentinel & Finance",
    badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    border: "border-emerald-500/30",
    glow: "shadow-emerald-950/40",
    accent: "text-emerald-400",
  },
};

export function getPersonaTheme(slug?: string): PersonaTheme {
  const normalized = (slug || "").toLowerCase().trim();
  return (
    PERSONA_THEMES[normalized] || {
      slug: normalized || "unknown",
      name: slug || "Agent",
      role: "AI Agent",
      badge: "bg-slate-800 text-slate-300 border-slate-700",
      border: "border-slate-800",
      glow: "shadow-slate-950/40",
      accent: "text-slate-400",
    }
  );
}

export function formatLatency(ms?: number): string {
  if (ms === undefined || ms === null || isNaN(ms)) return "0ms";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export function formatTokenCount(count?: number): string {
  if (!count || isNaN(count)) return "0";
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(2)}M`;
  if (count >= 1_000) return `${(count / 1_000).toFixed(1)}k`;
  return count.toLocaleString();
}

/**
 * High-performance bounded RingBuffer for telemetry events to guarantee
 * deterministic memory footprint and eliminate garbage-collection pressure.
 */
export class RingBuffer<T> {
  private buffer: (T | undefined)[];
  private head = 0;
  private tail = 0;
  private size = 0;
  readonly capacity: number;

  constructor(capacity: number) {
    this.capacity = Math.max(1, capacity);
    this.buffer = new Array(this.capacity);
  }

  push(item: T): void {
    this.buffer[this.tail] = item;
    this.tail = (this.tail + 1) % this.capacity;
    if (this.size < this.capacity) {
      this.size++;
    } else {
      this.head = (this.head + 1) % this.capacity;
    }
  }

  toArray(): T[] {
    const result: T[] = new Array(this.size);
    for (let i = 0; i < this.size; i++) {
      result[i] = this.buffer[(this.head + i) % this.capacity] as T;
    }
    return result;
  }

  toReverseArray(): T[] {
    const result: T[] = new Array(this.size);
    for (let i = 0; i < this.size; i++) {
      const idx = (this.tail - 1 - i + this.capacity) % this.capacity;
      result[i] = this.buffer[idx] as T;
    }
    return result;
  }

  clear(): void {
    this.buffer.fill(undefined);
    this.head = 0;
    this.tail = 0;
    this.size = 0;
  }

  get length(): number {
    return this.size;
  }
}
