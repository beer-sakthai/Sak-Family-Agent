/**
 * The activity calendar.
 *
 * `buildHeatmap` is where the bugs live — a fixed window over a sparse series
 * is an off-by-one in three directions at once — so most of this exercises it
 * directly with a pinned "today", and the render tests only check that the
 * component says out loud what the grid draws silently.
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ActivityHeatmap, { buildHeatmap, longestStreak } from "@/components/ActivityHeatmap";
import type { TrendPoint } from "@/lib/contracts.generated";

const TODAY = new Date("2026-08-31T13:45:00Z");

function point(date: string, runs: number, errors = 0): TrendPoint {
  return { date, runs, errors, avg_latency_ms: 1200, input_tokens: 10, output_tokens: 4 };
}

describe("buildHeatmap", () => {
  it("returns exactly the requested number of days", () => {
    expect(buildHeatmap([], 90, TODAY)).toHaveLength(90);
    expect(buildHeatmap([], 30, TODAY)).toHaveLength(30);
  });

  it("ends on today and starts days-1 back, in the trend series' UTC calendar", () => {
    const cells = buildHeatmap([], 7, TODAY);
    expect(cells[0].date).toBe("2026-08-25");
    expect(cells[6].date).toBe("2026-08-31");
  });

  it("places a recorded day on its own date rather than by position", () => {
    // A three-point series inside a seven-day window: the gaps have to land
    // where the calendar puts them, not be packed against one end.
    const cells = buildHeatmap(
      [point("2026-08-25", 4), point("2026-08-28", 9), point("2026-08-31", 1)],
      7,
      TODAY,
    );
    expect(cells.map((cell) => cell.runs)).toEqual([4, 0, 0, 9, 0, 0, 1]);
  });

  it("distinguishes a day reported as zero from a day never reported", () => {
    const cells = buildHeatmap([point("2026-08-30", 0)], 2, TODAY);
    expect(cells[0]).toMatchObject({ date: "2026-08-30", runs: 0, recorded: true, level: 0 });
    expect(cells[1]).toMatchObject({ date: "2026-08-31", runs: 0, recorded: false, level: 0 });
  });

  it("scales levels against the busiest day, so a quiet family still has contrast", () => {
    const cells = buildHeatmap(
      [
        point("2026-08-28", 1),
        point("2026-08-29", 4),
        point("2026-08-30", 7),
        point("2026-08-31", 10),
      ],
      4,
      TODAY,
    );
    expect(cells.map((cell) => cell.level)).toEqual([1, 2, 3, 4]);
  });

  it("never puts a run count above level 0 at level 0, however small", () => {
    // One run against a peak of a thousand is still a day something happened,
    // and a floor of 1 is what keeps it from disappearing into the empty days.
    const cells = buildHeatmap([point("2026-08-30", 1), point("2026-08-31", 1000)], 2, TODAY);
    expect(cells[0].level).toBe(1);
  });

  it("ignores days outside the window rather than folding them in", () => {
    const cells = buildHeatmap([point("2020-01-01", 999)], 3, TODAY);
    expect(cells.every((cell) => cell.runs === 0)).toBe(true);
  });

  it("carries the error count through for the day's tooltip", () => {
    const cells = buildHeatmap([point("2026-08-31", 10, 3)], 1, TODAY);
    expect(cells[0].errors).toBe(3);
  });
});

describe("longestStreak", () => {
  const cells = (runs: number[]) =>
    runs.map((count, index) => ({
      date: `2026-08-${String(index + 1).padStart(2, "0")}`,
      runs: count,
      errors: 0,
      level: count > 0 ? 1 : 0,
      recorded: true,
    }));

  it("counts the longest unbroken run, not the last one", () => {
    expect(longestStreak(cells([1, 1, 1, 0, 1, 1]))).toBe(3);
  });

  it("is zero for a window with nothing in it", () => {
    expect(longestStreak(cells([0, 0, 0]))).toBe(0);
    expect(longestStreak([])).toBe(0);
  });

  it("counts a streak that runs to the end of the window", () => {
    expect(longestStreak(cells([0, 1, 1, 1]))).toBe(3);
  });

  it("treats a zero day as a break, however it came to be zero", () => {
    expect(longestStreak(cells([1, 0, 1]))).toBe(1);
  });
});

describe("ActivityHeatmap", () => {
  const trends = [point("2026-08-29", 3), point("2026-08-30", 8), point("2026-08-31", 2)];

  it("summarises the grid in text, which is what a screen reader gets", () => {
    render(<ActivityHeatmap trends={trends} days={7} today={TODAY} />);
    expect(screen.getByText(/13 runs across 3 of the last 7 days/)).toBeInTheDocument();
  });

  it("names the busiest day rather than only the total", () => {
    render(<ActivityHeatmap trends={trends} days={7} today={TODAY} />);
    expect(screen.getByText(/busiest 2026-08-30 with 8/)).toBeInTheDocument();
  });

  it("says a quiet window is quiet instead of rendering a blank panel", () => {
    render(<ActivityHeatmap trends={[]} days={30} today={TODAY} />);
    expect(screen.getByText("No runs recorded in the last 30 days.")).toBeInTheDocument();
  });

  it("draws one cell per day in the window", () => {
    const { container } = render(<ActivityHeatmap trends={trends} days={14} today={TODAY} />);
    expect(container.querySelectorAll("[data-level]")).toHaveLength(14);
  });

  it("labels each recorded cell with its date and count", () => {
    const { container } = render(<ActivityHeatmap trends={trends} days={7} today={TODAY} />);
    const titles = [...container.querySelectorAll("[data-level]")].map((cell) =>
      cell.getAttribute("title"),
    );
    expect(titles).toContain("2026-08-30: 8 runs");
    expect(titles).toContain("2026-08-25: no data");
  });

  it("mentions errors in a day's label only when there were some", () => {
    const { container } = render(
      <ActivityHeatmap trends={[point("2026-08-31", 5, 2)]} days={1} today={TODAY} />,
    );
    expect(container.querySelector("[data-level]")?.getAttribute("title")).toBe(
      "2026-08-31: 5 runs, 2 with errors",
    );
  });

  it("states the figures the calendar implies but cannot show", () => {
    render(<ActivityHeatmap trends={trends} days={7} today={TODAY} />);
    // Three consecutive recorded days, ending today.
    expect(screen.getByText("Longest streak").nextSibling).toHaveTextContent("3days");
    expect(screen.getByText("Active days").nextSibling).toHaveTextContent("3of 7");
    // 13 runs over 3 active days.
    expect(screen.getByText("Per active day").nextSibling).toHaveTextContent("4runs");
  });

  it("shows an em dash rather than a division by zero for an empty window", () => {
    render(<ActivityHeatmap trends={[]} days={30} today={TODAY} />);
    expect(screen.getByText("Per active day").nextSibling).toHaveTextContent("—runs");
    expect(screen.queryByText(/NaN/)).not.toBeInTheDocument();
  });

  it("renders identically across repeated renders", () => {
    const first = render(<ActivityHeatmap trends={trends} days={30} today={TODAY} />).container
      .innerHTML;
    const second = render(<ActivityHeatmap trends={trends} days={30} today={TODAY} />).container
      .innerHTML;
    expect(first).toBe(second);
  });
});
