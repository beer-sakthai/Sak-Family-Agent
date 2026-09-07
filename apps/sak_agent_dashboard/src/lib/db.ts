/**
 * Read-only SQLite access to a memory shard.
 *
 * Three things this fixes over what it replaces:
 *
 *  - It used CommonJS `require("better-sqlite3")` inside an ESM module. Under
 *    Vitest's ESM transform `require` is undefined, so every call threw and was
 *    swallowed into a demo-data fallback — meaning the SQLite path had never
 *    once executed under test.
 *  - `db.close()` was skipped whenever an error escaped the inner try/catches,
 *    leaking the handle.
 *  - A missing database and a genuinely broken one were indistinguishable, both
 *    silently becoming fake data.
 *
 * `openDb` returns `null` for "no such shard" — a normal state, since a shard
 * file only exists once a persona has been written to — and lets a real error
 * propagate so the caller can report it instead of inventing data.
 */

import fs from "fs";

import Database from "better-sqlite3";

/** The subset of better-sqlite3 we use, so callers need no `any`. */
export interface ReadonlyDatabase {
  prepare(sql: string): {
    get(...params: unknown[]): Record<string, unknown> | undefined;
    all(...params: unknown[]): Record<string, unknown>[];
  };
  close(): void;
}

/**
 * Open `file` read-only, run `read`, and always close the handle.
 *
 * Returns null when the shard does not exist. Anything else — a corrupt file, a
 * missing native binding — throws, so the route reports a failure rather than
 * serving plausible fiction.
 *
 * `better-sqlite3` is a native addon, so `next.config.mjs` lists it in
 * `serverExternalPackages` to keep it out of the bundle; this module is only
 * ever reached from a route handler declaring `runtime = "nodejs"`.
 */
export function openDb<T>(file: string, read: (db: ReadonlyDatabase) => T): T | null {
  if (!fs.existsSync(file)) return null;

  const db = new Database(file, { readonly: true, fileMustExist: true }) as ReadonlyDatabase;
  try {
    return read(db);
  } finally {
    // finally, not the happy path only — the old code leaked on the error path.
    db.close();
  }
}
