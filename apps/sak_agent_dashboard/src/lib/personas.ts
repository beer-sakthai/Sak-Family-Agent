/**
 * The Sak Family roster — the single source of truth for this app.
 *
 * Keep `slug` aligned with `config.PERSONA_NAMES` in
 * `personas/sakthai/sakthai/config.py`, and keep `role` / `model` aligned with
 * each persona's `SOUL.md` roster line and `config/config.yaml`. Roles come from
 * the table in `personas/sakthai/SOUL.md`, which is CI-enforced for
 * cross-persona consistency by `tests/test_soul_consistency.py`.
 *
 * Nothing in this app may hard-code the roster length. Derive it from
 * `PERSONAS.length` so adding a seventh persona does not silently corrupt an
 * index-based aggregation the way a literal `5` did.
 */

export interface PersonaDescriptor {
  /** Matches config.PERSONA_NAMES — the on-disk directory and memory-shard name. */
  slug: string;
  /** Display name. */
  name: string;
  /** Role, from the SOUL.md roster table. */
  role: string;
  /** Configured default model, from the persona's config/config.yaml. */
  model: string;
  /** Configured default provider, from the same file. */
  provider: string;
  skills: string[];
  badge: string;
}

export const PERSONAS: readonly PersonaDescriptor[] = [
  {
    slug: "sakthai",
    name: "SakThai",
    role: "Main Lead, HF Master, Orchestrator",
    model: "gemini-3.1-flash-lite",
    provider: "huggingface",
    skills: ["routing", "planning", "hugging-face", "incident-command"],
    badge: "Lead",
  },
  {
    slug: "sakking",
    name: "SakKing",
    role: "General Assistant & Runner · Deputy 1",
    model: "Qwen/Qwen3-Coder-30B-A3B-Instruct",
    provider: "huggingface",
    skills: ["command-execution", "coordination", "research"],
    badge: "Deputy 1",
  },
  {
    slug: "saksee",
    name: "SakSee",
    role: "Web / Browser Specialist · Deputy 3",
    model: "gemini-3.1-flash-lite",
    provider: "huggingface",
    skills: ["browsing", "scraping", "monitoring"],
    badge: "Deputy 3",
  },
  {
    slug: "saksit",
    name: "SakSit",
    role: "Social / Content Specialist",
    model: "DeepSeek-V4-Flash",
    provider: "huggingface",
    skills: ["writing", "content", "publishing"],
    badge: "Content",
  },
  {
    slug: "sakjules",
    name: "SakJules",
    role: "GitHub, CI/CD & Automation",
    model: "gemini-2.5-flash-lite",
    provider: "huggingface",
    skills: ["ci-cd", "automation", "pull-requests"],
    badge: "Automation",
  },
  {
    slug: "saktan",
    name: "SakTan",
    role: "Daily Ops · Deputy 2",
    model: "sakthai",
    provider: "ollama",
    skills: ["daily-ops", "routine", "scheduling"],
    badge: "Deputy 2",
  },
] as const;

export const PERSONA_COUNT = PERSONAS.length;

/** Bucket for runs that carry no usable persona attribution. */
export const UNATTRIBUTED = "unattributed" as const;

export type PersonaSlug = string;

const BY_SLUG = new Map(PERSONAS.map((p) => [p.slug, p]));

/** Slugs longest-first, so no slug that is a prefix of another wins early. */
const BY_SPECIFICITY = [...PERSONAS].sort((a, b) => b.slug.length - a.slug.length);

export function personaBySlug(slug: string): PersonaDescriptor | undefined {
  return BY_SLUG.get(slug.toLowerCase());
}

export function personaIndex(slug: string): number {
  return PERSONAS.findIndex((p) => p.slug === slug.toLowerCase());
}

/** Display name for a slug, falling back to the slug itself. */
export function personaName(slug: string): string {
  return personaBySlug(slug)?.name ?? slug;
}

/**
 * Resolve a log entry to a persona slug, or `null` when it cannot be resolved.
 *
 * Returning `null` is the point. The previous implementation fell back to
 * `index % 5`, which round-robin-assigned unattributed runs across the roster
 * and fed the result straight into per-persona run counts and latency averages —
 * so those figures were part measurement, part fabrication, with nothing marking
 * which was which.
 *
 * Only explicit identity fields are trusted. Model names are deliberately NOT
 * used as a fallback: several personas share a model (SakThai and SakSee are
 * both `gemini-3.1-flash-lite`), so a model name cannot identify a persona.
 */
export function resolvePersonaSlug(entry: {
  persona?: unknown;
  agent?: unknown;
}): PersonaSlug | null {
  for (const raw of [entry.persona, entry.agent]) {
    if (typeof raw !== "string" || raw.trim().length === 0) continue;
    const value = raw.trim().toLowerCase();

    const exact = BY_SLUG.get(value);
    if (exact) return exact.slug;

    const partial = BY_SPECIFICITY.find((p) => value.includes(p.slug));
    if (partial) return partial.slug;
  }
  return null;
}
