/**
 * Property-based fuzzing of the URL-fragment parser.
 *
 * The fragment is the one input on the page anybody can edit — a pasted link,
 * a bookmark, a hand-typed `#sessions?page=…` — and `parseView` promises to
 * turn any string at all into a view that is safe to fetch with. The example
 * tests in url-state.test.ts pin specific cases; these throw arbitrary strings
 * and arbitrary valid views at it and check the promises hold for all of them.
 */
import fc from "fast-check";
import { describe, expect, it } from "vitest";

import { PERSONA_NAMES } from "@/lib/contracts.generated";
import { NAV_ITEMS, isTabId } from "@/lib/nav";
import { TREND_WINDOWS, parseView, serializeView, type ViewState } from "@/lib/url-state";

const PERSONAS: readonly string[] = PERSONA_NAMES;

/** A fragment shaped like the real thing: a section, then key=value pairs. */
const fragment = fc.oneof(
  fc.string(),
  fc
    .tuple(
      fc.oneof(fc.constantFrom(...NAV_ITEMS.map((item) => item.id)), fc.string()),
      fc.dictionary(
        fc.constantFrom("q", "severity", "page", "persona", "session", "run", "agent", "demo", "trend"),
        fc.oneof(
          fc.string(),
          fc.integer().map(String),
          // Past Number.MAX_SAFE_INTEGER, parseInt stops being exact.
          fc.stringMatching(/^[1-9][0-9]{15,30}$/),
          fc.constantFrom(...PERSONAS),
        ),
      ),
    )
    .map(([tab, params]) => `${tab}?${new URLSearchParams(params).toString()}`),
);

/** Any view the page itself can produce. */
const validView: fc.Arbitrary<ViewState> = fc.record({
  tab: fc.constantFrom(...NAV_ITEMS.map((item) => item.id)),
  search: fc.string(),
  severity: fc.string(),
  page: fc.integer({ min: 1, max: Number.MAX_SAFE_INTEGER }),
  personas: fc.uniqueArray(fc.constantFrom(...PERSONAS)),
  session: fc.option(fc.string({ minLength: 1 }), { nil: null }),
  run: fc.option(fc.string({ minLength: 1 }), { nil: null }),
  agent: fc.option(fc.constantFrom(...PERSONAS), { nil: null }),
  demo: fc.boolean(),
  trend: fc.constantFrom(...TREND_WINDOWS),
});

describe("parseView (fuzzed)", () => {
  it("turns any fragment into a sanitised view", () => {
    fc.assert(
      fc.property(fragment, (hash) => {
        const view = parseView(hash);
        expect(isTabId(view.tab)).toBe(true);
        expect(Number.isSafeInteger(view.page) && view.page >= 1).toBe(true);
        expect(view.personas.every((p) => PERSONAS.includes(p))).toBe(true);
        expect(new Set(view.personas).size).toBe(view.personas.length);
        expect(view.agent === null || PERSONAS.includes(view.agent)).toBe(true);
        expect((TREND_WINDOWS as readonly number[]).includes(view.trend)).toBe(true);
        expect(typeof view.demo).toBe("boolean");
      }),
    );
  });

  it("reads back every view it serialises", () => {
    fc.assert(
      fc.property(validView, (view) => {
        expect(parseView(serializeView(view))).toEqual(view);
      }),
    );
  });

  it("is stable once a fragment has been through it", () => {
    // `patch` re-serialises the parsed view, so this is what a click does to
    // a pasted link: it must not move anything the user did not change.
    fc.assert(
      fc.property(fragment, (hash) => {
        const view = parseView(hash);
        expect(parseView(serializeView(view))).toEqual(view);
      }),
    );
  });
});
