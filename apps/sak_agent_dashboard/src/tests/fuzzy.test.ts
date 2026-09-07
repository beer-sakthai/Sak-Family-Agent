/**
 * The command palette's matcher.
 *
 * Kept apart from the palette's own render tests: the ranking rules are the
 * part with behaviour worth pinning, and they are testable without a DOM.
 */

import { describe, expect, it } from "vitest";

import { fuzzyMatch, highlightSegments, rankBy } from "@/lib/fuzzy";

describe("fuzzyMatch", () => {
  it("matches a subsequence, not just a substring", () => {
    expect(fuzzyMatch("usd", "Use sample data")).not.toBeNull();
    expect(fuzzyMatch("ovw", "Overview")).not.toBeNull();
  });

  it("still matches a plain substring", () => {
    expect(fuzzyMatch("memo", "Memory")).not.toBeNull();
  });

  it("refuses a query whose characters are out of order", () => {
    expect(fuzzyMatch("weivrevo", "Overview")).toBeNull();
    expect(fuzzyMatch("zzz", "Overview")).toBeNull();
  });

  it("matches everything on an empty query, so an unfiltered list stays whole", () => {
    expect(fuzzyMatch("", "anything")).toEqual({ score: 0, positions: [] });
  });

  it("ignores case in both directions", () => {
    expect(fuzzyMatch("MEM", "Memory")).not.toBeNull();
    expect(fuzzyMatch("mem", "MEMORY")).not.toBeNull();
  });

  it("scores a prefix above the same characters buried later", () => {
    const prefix = fuzzyMatch("mem", "Memory")!;
    const buried = fuzzyMatch("mem", "A very long label about memory")!;
    expect(prefix.score).toBeGreaterThan(buried.score);
  });

  it("scores consecutive characters above scattered ones", () => {
    const run = fuzzyMatch("audit", "Audit")!;
    const scattered = fuzzyMatch("audit", "A useful description in transit")!;
    expect(run.score).toBeGreaterThan(scattered.score);
  });

  it("reports where it matched, so the row can show why", () => {
    expect(fuzzyMatch("mo", "Memory")!.positions).toEqual([0, 3]);
  });
});

describe("highlightSegments", () => {
  it("splits a label into matched and unmatched runs", () => {
    expect(highlightSegments("Memory", [0, 1])).toEqual([
      { text: "Me", matched: true },
      { text: "mory", matched: false },
    ]);
  });

  it("returns the whole string as one unmatched run when nothing matched", () => {
    expect(highlightSegments("Memory", [])).toEqual([{ text: "Memory", matched: false }]);
  });

  it("reassembles to the original string", () => {
    const segments = highlightSegments("Use sample data", [0, 1, 4]);
    expect(segments.map((segment) => segment.text).join("")).toBe("Use sample data");
  });
});

describe("rankBy", () => {
  const items = [
    { label: "Sessions", hint: "Recorded agent runs" },
    { label: "Overview", hint: "Every session at a glance" },
  ];
  const fields = (item: (typeof items)[number]) => [item.label, item.hint];

  it("ranks a label hit above a description hit", () => {
    const ranked = rankBy(items, "session", fields);
    expect(ranked[0].item.label).toBe("Sessions");
    expect(ranked[0].fieldIndex).toBe(0);
    expect(ranked[1].fieldIndex).toBe(1);
  });

  it("drops items that match no field at all", () => {
    expect(rankBy(items, "workflow", fields)).toHaveLength(0);
  });

  it("keeps the declared order when every item scores the same", () => {
    const ranked = rankBy(items, "", fields);
    expect(ranked.map((entry) => entry.item.label)).toEqual(["Sessions", "Overview"]);
  });
});
