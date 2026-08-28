import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { clearChartTokenCache } from "@/lib/chart-theme";

/**
 * `useChartTokens` is a hook over `getComputedStyle`, and jsdom does not
 * resolve CSS variables from a stylesheet. What is testable — and what
 * actually broke the light theme — is the reader's behaviour when a variable
 * is present, absent, or changed, so the tokens are set inline on <html>.
 */
async function readTokens() {
  clearChartTokenCache();
  // Imported fresh each time so the module's own cache cannot leak between
  // assertions in a way the explicit clear would not catch.
  const { useChartTokens } = await import("@/lib/chart-theme");
  const { renderHook } = await import("@testing-library/react");
  const { result } = renderHook(() => useChartTokens());
  return result.current;
}

describe("useChartTokens", () => {
  beforeEach(() => {
    clearChartTokenCache();
    document.documentElement.removeAttribute("style");
  });

  afterEach(() => {
    document.documentElement.removeAttribute("style");
    clearChartTokenCache();
  });

  it("falls back to the dark palette when no variables are set", async () => {
    const tokens = await readTokens();
    expect(tokens.grid).toBe("rgb(30 41 59)");
    expect(tokens.axis).toBe("rgb(100 116 139)");
  });

  it("always offers six series colours", async () => {
    const tokens = await readTokens();
    expect(tokens.series).toHaveLength(6);
    expect(tokens.series.every((colour) => colour.startsWith("rgb("))).toBe(true);
  });

  it("wraps a bare channel triple as an rgb() colour", async () => {
    document.documentElement.style.setProperty("--line", "1 2 3");
    const tokens = await readTokens();
    expect(tokens.grid).toBe("rgb(1 2 3)");
  });

  it("reads each role from its own variable", async () => {
    document.documentElement.style.setProperty("--panel", "10 20 30");
    document.documentElement.style.setProperty("--line-strong", "40 50 60");
    document.documentElement.style.setProperty("--fg", "70 80 90");
    const tokens = await readTokens();
    expect(tokens.tooltipBackground).toBe("rgb(10 20 30)");
    expect(tokens.tooltipBorder).toBe("rgb(40 50 60)");
    expect(tokens.tooltipText).toBe("rgb(70 80 90)");
  });

  it("reads the series colours from the hue tokens", async () => {
    document.documentElement.style.setProperty("--h-cyan", "1 1 1");
    document.documentElement.style.setProperty("--h-rose", "5 5 5");
    const tokens = await readTokens();
    expect(tokens.series[0]).toBe("rgb(1 1 1)");
    expect(tokens.series[4]).toBe("rgb(5 5 5)");
  });

  it("falls back per role, not all-or-nothing", async () => {
    // One unset variable must not drag the rest back to the defaults.
    document.documentElement.style.setProperty("--line", "9 9 9");
    const tokens = await readTokens();
    expect(tokens.grid).toBe("rgb(9 9 9)");
    expect(tokens.axis).toBe("rgb(100 116 139)");
  });

  it("re-reads after the cache is cleared", async () => {
    document.documentElement.style.setProperty("--line", "1 1 1");
    expect((await readTokens()).grid).toBe("rgb(1 1 1)");

    document.documentElement.style.setProperty("--line", "2 2 2");
    expect((await readTokens()).grid).toBe("rgb(2 2 2)");
  });
});
