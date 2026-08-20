import { describe, it, expect } from "vitest";
import {
  PERSONA_THEMES,
  getPersonaTheme,
  formatLatency,
  formatTokenCount,
  RingBuffer,
} from "@/lib/uiUtils";

describe("UI Utilities & Theme Refactor", () => {
  it("provides complete themes for all 6 personas", () => {
    const personas = ["sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan"];
    personas.forEach((p) => {
      const theme = getPersonaTheme(p);
      expect(theme.slug).toBe(p);
      expect(theme.name).toBeDefined();
      expect(theme.badge).toContain("border");
    });
  });

  it("handles unknown persona slugs gracefully with fallback theme", () => {
    const theme = getPersonaTheme("unknown_agent");
    expect(theme.slug).toBe("unknown_agent");
    expect(theme.name).toBe("unknown_agent");
    expect(theme.badge).toContain("bg-slate-800");
  });

  it("formats latency values accurately", () => {
    expect(formatLatency(0)).toBe("0ms");
    expect(formatLatency(450)).toBe("450ms");
    expect(formatLatency(1500)).toBe("1.50s");
    expect(formatLatency(undefined)).toBe("0ms");
  });

  it("formats token counts accurately", () => {
    expect(formatTokenCount(0)).toBe("0");
    expect(formatTokenCount(850)).toBe("850");
    expect(formatTokenCount(1250)).toBe("1.3k");
    expect(formatTokenCount(2500000)).toBe("2.50M");
    expect(formatTokenCount(undefined)).toBe("0");
  });

  it("RingBuffer maintains bounded capacity and FIFO ordering", () => {
    const rb = new RingBuffer<string>(3);
    expect(rb.length).toBe(0);
    expect(rb.toArray()).toEqual([]);

    rb.push("A");
    rb.push("B");
    expect(rb.length).toBe(2);
    expect(rb.toArray()).toEqual(["A", "B"]);
    expect(rb.toReverseArray()).toEqual(["B", "A"]);

    rb.push("C");
    expect(rb.length).toBe(3);
    expect(rb.toArray()).toEqual(["A", "B", "C"]);

    // Push 4th item -> "A" is evicted
    rb.push("D");
    expect(rb.length).toBe(3);
    expect(rb.toArray()).toEqual(["B", "C", "D"]);
    expect(rb.toReverseArray()).toEqual(["D", "C", "B"]);

    rb.clear();
    expect(rb.length).toBe(0);
    expect(rb.toArray()).toEqual([]);
  });
});
