/**
 * types/index.ts — Barrel that re-exports all dashboard types.
 *
 * Import from here (`@/lib/types`) to get all types. The sub-modules
 * (runtime, integrations, m365, ui) provide domain-scoped imports for
 * code that only needs a subset.
 *
 * NOTE: This barrel re-exports from the parent `types.ts` file, which
 * remains the source of truth during the incremental migration. Once
 * each type is moved into a sub-module, `types.ts` will be trimmed and
 * eventually deleted.
 */

// Re-export everything from the monolithic file so all existing
// `import { ... } from "@/lib/types"` imports continue to work unchanged.
export * from "../types";
