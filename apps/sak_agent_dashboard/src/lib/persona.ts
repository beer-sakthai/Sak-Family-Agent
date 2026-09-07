/**
 * `"sakthai"` -> `"SakThai"`.
 *
 * The same rule as `runtime.ts:displayName` and `web/api.py:display_name`, but
 * importable from a client component: `runtime.ts` reaches for `fs` and `os`
 * at module scope, so importing it from the browser bundle is not an option.
 */
export function displayName(persona: string): string {
  if (persona.length <= 3) return persona;
  return "Sak" + persona[3].toUpperCase() + persona.slice(4).toLowerCase();
}
