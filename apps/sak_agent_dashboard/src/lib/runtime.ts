/**
 * Where the SakThai runtime state lives, resolved in exactly one place.
 *
 * This used to be duplicated as `process.env.SAKTHAI_DIR || ~/.sakthai` in both
 * `lib/sakthai.ts` and `lib/db.ts` — under an environment variable the Python
 * package does not even read. `SAKTHAI_HOME` is the real one (see
 * `sakthai/config.py:sakthai_home`); `SAKTHAI_DIR` is kept working as a
 * deprecated alias so existing setups don't break.
 *
 * Nothing here is Next.js-specific; it is plain Node and only ever runs
 * server-side (the route handlers declare `runtime = "nodejs"`).
 */

import fs from "fs";
import os from "os";
import path from "path";

import { PERSONA_NAMES } from "./contracts.generated";

/** One runtime root: the unscoped home, or a single persona's own subtree. */
export interface RuntimeRoot {
  /** null for the unscoped root — state there attributes to no persona. */
  persona: string | null;
  path: string;
}

/**
 * The runtime root: `$SAKTHAI_HOME`, else the deprecated `$SAKTHAI_DIR`, else
 * `~/.sakthai`. Read per call rather than captured at module load, so tests can
 * point it at a fixture without reimporting the module graph.
 */
export function sakthaiHome(): string {
  const configured = process.env.SAKTHAI_HOME || process.env.SAKTHAI_DIR;
  return configured && configured.trim().length > 0
    ? configured
    : path.join(os.homedir(), ".sakthai");
}

/**
 * The unscoped root plus each persona's own root.
 *
 * Every deployed persona runs with `SAKTHAI_HOME=$HOME/.sakthai/$AGENT`
 * (`infra/vm-agents/sakthai-agent-run.sh`), so its sessions, eval log and audit
 * log live under its own subdirectory. A reader that only looks at the
 * unscoped root sees local dev runs and nothing else.
 */
export function runtimeRoots(home = sakthaiHome()): RuntimeRoot[] {
  return [
    { persona: null, path: home },
    ...PERSONA_NAMES.map((persona) => ({ persona, path: path.join(home, persona) })),
  ];
}

/** Whether the runtime root exists at all — the local source's precondition. */
export function runtimeAvailable(home = sakthaiHome()): boolean {
  try {
    return fs.statSync(home).isDirectory();
  } catch {
    return false;
  }
}

/**
 * `"sakthai"` -> `"SakThai"`. Mirrors `web/api.py:display_name`.
 *
 * Re-exported rather than defined here: client components need it too, and
 * this module touches `fs`/`os` at import time, so it cannot be one of their
 * dependencies. `persona.ts` holds the one definition.
 */
export { displayName } from "./persona";
