/**
 * types/index.ts — Barrel that re-exports all dashboard types.
 *
 * Import from here (`@/lib/types`) to get all types. The sub-modules
 * (runtime, integrations, m365, ui) hold the actual type definitions,
 * grouped by domain; import directly from a sub-module for a domain-scoped
 * subset.
 *
 * The monolithic `types.ts` this barrel used to defer to has been removed —
 * every type it defined now lives in exactly one of the four domain modules
 * below. The remaining `export *` lines re-export types that already lived
 * in their own domain directories under `src/lib/` (eval, a2a, cache,
 * mutation, adk/observability, redteam, voice, cycle) and were never part of
 * the monolith split.
 */

export * from "./runtime";
export * from "./integrations";
export * from "./m365";
export * from "./ui";

export * from "../eval/types";
export * from "../a2a/types";
export * from "../cache/types";
export * from "../mutation/types";
export * from "../adk/observability_types";
export * from "../redteam/types";
export * from "../voice/types";
export * from "../cycle/types";
