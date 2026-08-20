import { DataSource } from "./types";

/**
 * Data-source resolution Strategy.
 *
 * The runtime data modules (`sakthai.ts`, `db.ts`) all made the same
 * three/four-way decision inline: serve demo data when `?demo=true`, serve
 * demo data labelled `"unavailable"` when the backing file/db is absent, serve
 * demo data labelled `"demo"` when the file/db exists but reading or parsing
 * it fails, and serve live data otherwise. That branch was copy-pasted into
 * every reader. `resolveDataSource` encodes it once; a module supplies a
 * `DataSourceStrategy` (how to read live, how to read demo) and the decision
 * is made here.
 */

/** Thrown by a strategy's `readLive` when the backing source does not exist. */
export class SourceUnavailableError extends Error {
  /**
   * Optional pre-built fallback payload. When a strategy needs the
   * "unavailable" response to carry more than plain demo data — e.g.
   * `db.ts`'s memory reader, which reports demo facts/observations plus the
   * real (all-absent) per-persona shard status list — it can attach that
   * payload here instead of `resolveDataSource` calling `readDemo()` blind.
   * Left unset, `resolveDataSource` falls back to `strategy.readDemo()`.
   */
  readonly fallback?: unknown;

  constructor(message = "Data source is not available", fallback?: unknown) {
    super(message);
    this.name = "SourceUnavailableError";
    this.fallback = fallback;
  }
}

/**
 * Thrown by a strategy's `readLive` when the backing source exists but could
 * not be read or parsed (truncated JSON, a corrupt DB file, a permission
 * error hit after the existence check, etc). Distinct from
 * `SourceUnavailableError`: the previous inline implementations in
 * `sakthai.ts` downgraded this case to `dataSource: "demo"`, not
 * `"unavailable"` — the source is there, it just couldn't be read this time —
 * and `resolveDataSource` preserves that distinction.
 */
export class SourceReadError extends Error {
  constructor(message = "Data source could not be read") {
    super(message);
    this.name = "SourceReadError";
  }
}

/** How to read one data source in its two modes. */
export interface DataSourceStrategy<T> {
  /** Read the real source. Throw `SourceUnavailableError` when it is absent. */
  readLive(): Promise<T>;
  /** Produce the demo fallback. */
  readDemo(): T;
}

export interface DataSourceResult<T> {
  data: T;
  dataSource: DataSource;
}

/**
 * Resolve a data source to `demo`, `unavailable`, or `live`.
 *
 * - `demo` → `readDemo()` labelled `"demo"`.
 * - source absent (`readLive` throws `SourceUnavailableError`) → the error's
 *   attached `fallback`, or else `readDemo()`, labelled `"unavailable"` — the
 *   UI still renders, but the badge tells the truth that the numbers are not
 *   measured.
 * - source present but unreadable (`readLive` throws `SourceReadError`) →
 *   `readDemo()` labelled `"demo"` — matches the pre-Strategy behaviour of
 *   `sakthai.ts`, which downgraded a read/parse failure to demo data rather
 *   than a 500.
 * - otherwise → `readLive()` labelled `"live"`.
 *
 * Any error other than `SourceUnavailableError`/`SourceReadError` propagates,
 * so a genuine bug in a strategy's own code still surfaces as a 500 rather
 * than being silently masked as demo data.
 */
export async function resolveDataSource<T>(
  strategy: DataSourceStrategy<T>,
  demo: boolean,
): Promise<DataSourceResult<T>> {
  if (demo) {
    return { data: strategy.readDemo(), dataSource: "demo" };
  }
  try {
    return { data: await strategy.readLive(), dataSource: "live" };
  } catch (error) {
    if (error instanceof SourceUnavailableError) {
      const data = (error.fallback !== undefined ? error.fallback : strategy.readDemo()) as T;
      return { data, dataSource: "unavailable" };
    }
    if (error instanceof SourceReadError) {
      return { data: strategy.readDemo(), dataSource: "demo" };
    }
    throw error;
  }
}
