"use client";

import React, { useMemo } from "react";
import { CalendarDays } from "lucide-react";

import type { TrendPoint } from "@/lib/contracts.generated";

/** Five steps, quiet to loud. Spelled out so Tailwind's scanner sees them. */
const LEVEL_CLASS = [
  "bg-raised/70",
  "bg-hue-emerald/25",
  "bg-hue-emerald/45",
  "bg-hue-emerald/70",
  "bg-hue-emerald",
] as const;

const WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

export interface HeatmapCell {
  /** `YYYY-MM-DD`, in the same UTC calendar the trend series uses. */
  date: string;
  runs: number;
  errors: number;
  /** 0..4. 0 means no recorded runs, not "few". */
  level: number;
  /** Whether the source reported this day at all. */
  recorded: boolean;
}

/**
 * Turn a trend series into a fixed grid of the last `days` calendar days.
 *
 * Exported for its own test: the awkward parts — a series with gaps, a series
 * shorter than the window, a run count that is zero rather than absent — are
 * all off-by-one hazards, and they are far easier to pin here than through a
 * rendered grid.
 *
 * Days the source never reported and days it reported as zero both draw at
 * level 0; `recorded` distinguishes them for the tooltip, so an unreported day
 * says "no data" rather than claiming a confident zero.
 */
export function buildHeatmap(
  trends: readonly TrendPoint[],
  days: number,
  today = new Date(),
): HeatmapCell[] {
  const byDate = new Map(trends.map((point) => [point.date, point]));

  // Peak sets the top of the scale, so a quiet family still shows contrast
  // instead of a uniformly dim grid. Thresholds are fractions of the peak.
  const peak = trends.reduce((max, point) => Math.max(max, point.runs), 0);

  // Anchored on UTC midnight: the trend dates are UTC calendar days, and
  // building the window in local time would shift the whole grid by one for
  // anyone west of Greenwich.
  const end = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());

  const cells: HeatmapCell[] = [];
  for (let offset = days - 1; offset >= 0; offset -= 1) {
    const at = new Date(end - offset * 86_400_000);
    const date = at.toISOString().slice(0, 10);
    const point = byDate.get(date);
    const runs = point?.runs ?? 0;

    let level = 0;
    if (runs > 0 && peak > 0) {
      const ratio = runs / peak;
      level = ratio > 0.75 ? 4 : ratio > 0.5 ? 3 : ratio > 0.25 ? 2 : 1;
    }

    cells.push({ date, runs, errors: point?.errors ?? 0, level, recorded: point !== undefined });
  }
  return cells;
}

/**
 * The longest unbroken run of days with at least one recorded run.
 *
 * A day the source never reported breaks the streak, the same as a reported
 * zero: we know the family did nothing *or* we know nothing, and neither is a
 * day to count towards a run of activity.
 */
export function longestStreak(cells: readonly HeatmapCell[]): number {
  let best = 0;
  let current = 0;
  for (const cell of cells) {
    current = cell.runs > 0 ? current + 1 : 0;
    if (current > best) best = current;
  }
  return best;
}

interface ActivityHeatmapProps {
  trends: readonly TrendPoint[];
  /** How many calendar days the grid covers. */
  days?: number;
  /** Pinned in tests; defaults to the real clock. */
  today?: Date;
}

/**
 * A calendar of recorded runs — the family's pulse at a glance.
 *
 * The Analytics charts answer "how much" precisely and "when" badly: a line of
 * thirty points tells you the shape of a month but not that nothing ran for
 * the four days before last Tuesday. This does the opposite, and it is the
 * thing people actually look at first.
 *
 * Drawn as a plain grid of `<div>`s rather than a chart library: at 90 cells
 * of 11px a Recharts container costs a measurement pass for a picture with no
 * axes, no scales, and nothing to hover beyond a title.
 *
 * The grid is `aria-hidden` and the accessible content is the summary below
 * it — a screen reader gets "182 runs across 34 of the last 90 days, busiest
 * 2026-08-14", which is the whole of what the picture says, rather than
 * ninety unlabelled cells.
 */
export function ActivityHeatmap({ trends, days = 90, today }: ActivityHeatmapProps) {
  const cells = useMemo(() => buildHeatmap(trends, days, today), [trends, days, today]);

  const totalRuns = cells.reduce((sum, cell) => sum + cell.runs, 0);
  const activeDays = cells.filter((cell) => cell.runs > 0).length;
  const busiest = cells.reduce<HeatmapCell | null>(
    (best, cell) => (cell.runs > 0 && (best === null || cell.runs > best.runs) ? cell : best),
    null,
  );
  const streak = longestStreak(cells);

  // Columns are weeks. The first column is padded so every row is one weekday,
  // which is what makes a weekly rhythm — quiet weekends, busy Mondays —
  // visible as a horizontal band rather than a diagonal.
  const leadIn = cells.length > 0 ? new Date(`${cells[0].date}T00:00:00Z`).getUTCDay() : 0;
  const columns: (HeatmapCell | null)[][] = [];
  let column: (HeatmapCell | null)[] = Array.from({ length: leadIn }, () => null);
  for (const cell of cells) {
    column.push(cell);
    if (column.length === 7) {
      columns.push(column);
      column = [];
    }
  }
  if (column.length > 0) {
    while (column.length < 7) column.push(null);
    columns.push(column);
  }

  const summary =
    totalRuns === 0
      ? `No runs recorded in the last ${days} days.`
      : `${totalRuns.toLocaleString()} runs across ${activeDays} of the last ${days} days` +
        (busiest ? `, busiest ${busiest.date} with ${busiest.runs.toLocaleString()}.` : ".");

  return (
    <section
      data-panel
      data-testid="activity-heatmap"
      className="rounded-2xl border border-line/80 bg-panel/70 p-pad backdrop-blur-xl"
      aria-label={`Run activity over the last ${days} days`}
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="flex items-center gap-1.5 font-display text-sm font-bold text-fg-2">
          <CalendarDays className="h-4 w-4 text-hue-emerald" aria-hidden />
          Activity
        </h3>
        <p className="font-mono text-[11px] text-fg-4">{summary}</p>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-x-8 gap-y-4">
        <div className="flex gap-2 overflow-x-auto pb-1">
          <div
            className="grid shrink-0 grid-rows-[repeat(7,11px)] gap-[3px] pt-0.5 font-mono text-[9px] text-fg-5"
            aria-hidden
          >
            {WEEKDAY_LABELS.map((label, index) => (
              // Every other row is labelled: seven 11px rows cannot carry seven
              // legible labels, and Mon/Wed/Fri is the convention.
              <span key={label} className="h-[11px] leading-[11px]">
                {index % 2 === 1 ? label : ""}
              </span>
            ))}
          </div>

          <div className="flex gap-[3px]" aria-hidden>
            {columns.map((week, weekIndex) => (
              <div key={weekIndex} className="grid grid-rows-[repeat(7,11px)] gap-[3px]">
                {week.map((cell, dayIndex) =>
                  cell === null ? (
                    <span key={dayIndex} className="h-[11px] w-[11px]" />
                  ) : (
                    <span
                      key={cell.date}
                      title={
                        cell.recorded
                          ? `${cell.date}: ${cell.runs} run${cell.runs === 1 ? "" : "s"}${
                              cell.errors > 0 ? `, ${cell.errors} with errors` : ""
                            }`
                          : `${cell.date}: no data`
                      }
                      data-level={cell.level}
                      className={`h-[11px] w-[11px] rounded-[2px] border border-line-soft/60 ${LEVEL_CLASS[cell.level]}`}
                    />
                  ),
              )}
            </div>
            ))}
          </div>
        </div>

        {/* The figures the picture implies but cannot state. They fill the
            width a thirteen-week grid leaves over on a wide panel, and they
            are the numbers someone reads the calendar to find. */}
        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 font-mono text-[11px] sm:grid-cols-4">
          <div>
            <dt className="text-[10px] uppercase tracking-wider text-fg-4">Active days</dt>
            <dd className="font-display text-base font-bold text-fg">
              {activeDays}
              <span className="ml-1 font-mono text-[10px] font-normal text-fg-4">of {days}</span>
            </dd>
          </div>
          <div>
            <dt className="text-[10px] uppercase tracking-wider text-fg-4">Longest streak</dt>
            <dd className="font-display text-base font-bold text-fg">
              {streak}
              <span className="ml-1 font-mono text-[10px] font-normal text-fg-4">
                {streak === 1 ? "day" : "days"}
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-[10px] uppercase tracking-wider text-fg-4">Busiest day</dt>
            <dd className="font-display text-base font-bold text-fg">
              {busiest ? busiest.runs.toLocaleString() : "—"}
              {busiest && (
                <span className="ml-1 font-mono text-[10px] font-normal text-fg-4">
                  {busiest.date.slice(5)}
                </span>
              )}
            </dd>
          </div>
          <div>
            <dt className="text-[10px] uppercase tracking-wider text-fg-4">Per active day</dt>
            <dd className="font-display text-base font-bold text-fg">
              {activeDays > 0 ? Math.round(totalRuns / activeDays).toLocaleString() : "—"}
              <span className="ml-1 font-mono text-[10px] font-normal text-fg-4">runs</span>
            </dd>
          </div>
        </dl>
      </div>

      <div className="mt-3 flex items-center justify-end gap-1.5 font-mono text-[10px] text-fg-5">
        <span aria-hidden>Less</span>
        {LEVEL_CLASS.map((className, level) => (
          <span
            key={level}
            aria-hidden
            className={`h-[11px] w-[11px] rounded-[2px] border border-line-soft/60 ${className}`}
          />
        ))}
        <span aria-hidden>More</span>
      </div>
    </section>
  );
}

export default ActivityHeatmap;
