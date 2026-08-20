import { DataSource } from "./types";

/**
 * Data-source resolution Strategy.
 *
 * The runtime data modules (`sakthai.ts`, `db.ts`) all made the same three-way
 * decision inline: serve demo data when `?demo=true`, serve demo data labelled
 * `"unavailable"` when the backing file/db is absent, and serve live data
 * otherwise. That branch was copy-pasted into every reader. `resolveDataSource`
 * encodes it once; a module supplies a `DataSourceStrategy` (how to read live,
 * how to read demo) and the decision is made here.
 */

/** Thrown by a strategy's `readLive` when the backing source does not exist. */
export class SourceUnavailableError extends Error {
  constructor(message = "Data source is not available") {
    super(message);
    this.name = "SourceUnavailableError";
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
 * - source absent (`readLive` throws `SourceUnavailableError`) → `readDemo()`
 *   labelled `"unavailable"` — the UI still renders, but the badge tells the
 *   truth that the numbers are not measured.
 * - otherwise → `readLive()` labelled `"live"`.
 *
 * Any error other than `SourceUnavailableError` propagates, so a genuine read
 * failure still surfaces as a 500 rather than being masked as "unavailable".
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
      return { data: strategy.readDemo(), dataSource: "unavailable" };
    }
    throw error;
  }
}
