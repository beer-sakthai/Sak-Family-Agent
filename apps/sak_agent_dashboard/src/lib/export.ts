"use client";

/**
 * Download the panel you are looking at.
 *
 * The dashboard is read-only, which makes "get this into a spreadsheet" the
 * one thing people reliably want from it that it could not do. Both writers
 * work on the payload already in the browser, so an export never re-queries
 * and never shows a different set from the one on screen.
 */

/** Quote a CSV field per RFC 4180: double the quotes, wrap if it needs it. */
function csvField(value: unknown): string {
  if (value === null || value === undefined) return "";
  const text =
    typeof value === "object" ? JSON.stringify(value) : String(value as string | number | boolean);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/**
 * Rows to CSV, with `columns` fixing the order.
 *
 * Taking the column list explicitly rather than deriving it from the first
 * row's keys means a row missing an optional field cannot shift every later
 * column left by one.
 */
export function toCsv<T extends Record<string, unknown>>(
  rows: readonly T[],
  columns: readonly (keyof T & string)[],
): string {
  const header = columns.map(csvField).join(",");
  const body = rows.map((row) => columns.map((column) => csvField(row[column])).join(","));
  // CRLF: Excel treats a bare LF file as a single line in some locales.
  return [header, ...body].join("\r\n");
}

/**
 * Hand `content` to the browser as a file.
 *
 * The object URL is revoked on the next task rather than immediately: Safari
 * cancels the download if the URL dies in the same tick as the click.
 */
export function downloadFile(filename: string, content: string, mimeType: string): void {
  const url = URL.createObjectURL(new Blob([content], { type: `${mimeType};charset=utf-8` }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

/** `sak-sessions-2026-08-27.csv` — dated, so a folder of them stays sortable. */
export function exportFilename(panel: string, extension: string, at = new Date()): string {
  return `sak-${panel}-${at.toISOString().slice(0, 10)}.${extension}`;
}
