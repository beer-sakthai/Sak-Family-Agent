/**
 * Display formatting shared by the shell and the panels.
 *
 * Kept out of components so the rounding rules are testable on their own and
 * a millisecond count reads the same everywhere it appears.
 */

/** `1234` -> `"1.2k"`. Keeps a KPI tile from wrapping on a real token count. */
export function compactNumber(value: number): string {
  if (!Number.isFinite(value)) return "—";
  const abs = Math.abs(value);
  if (abs < 1_000) return String(Math.round(value));
  if (abs < 1_000_000) return `${(value / 1_000).toFixed(abs < 10_000 ? 1 : 0)}k`;
  if (abs < 1_000_000_000) return `${(value / 1_000_000).toFixed(abs < 10_000_000 ? 1 : 0)}M`;
  return `${(value / 1_000_000_000).toFixed(1)}B`;
}

/** Milliseconds as the largest unit that still reads precisely. */
export function duration(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return "—";
  if (ms < 1_000) return `${Math.round(ms)}ms`;
  if (ms < 60_000) return `${(ms / 1_000).toFixed(1)}s`;
  const minutes = Math.floor(ms / 60_000);
  const seconds = Math.round((ms % 60_000) / 1_000);
  return `${minutes}m ${seconds}s`;
}

/**
 * "3 minutes ago" from an epoch-milliseconds instant.
 *
 * `now` is a parameter rather than an implicit `Date.now()` so a test can pin
 * it; the shell passes a ticking clock so the label stays honest without the
 * component re-fetching.
 */
export function relativeTime(atMs: number, now = Date.now()): string {
  const seconds = Math.round((now - atMs) / 1_000);
  if (!Number.isFinite(seconds)) return "—";
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

/** A percentage with one decimal, or an em dash when there is nothing to rate. */
export function percent(value: number | null): string {
  return value === null || !Number.isFinite(value) ? "—" : `${value.toFixed(1)}%`;
}
