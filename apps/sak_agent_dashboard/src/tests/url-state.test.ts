import { describe, expect, it } from "vitest";

import { DEFAULT_VIEW, parseView, serializeView } from "@/lib/url-state";

describe("parseView", () => {
  it("reads a bare section", () => {
    expect(parseView("sessions").tab).toBe("sessions");
  });

  it("falls back to the default section for an unknown one", () => {
    expect(parseView("nonsense").tab).toBe(DEFAULT_VIEW.tab);
  });

  it("falls back for an empty fragment", () => {
    expect(parseView("")).toEqual(DEFAULT_VIEW);
  });

  it("reads the search text", () => {
    expect(parseView("sessions?q=deploy").search).toBe("deploy");
  });

  it("reads the severity filter", () => {
    expect(parseView("audit?severity=high").severity).toBe("high");
  });

  it("reads the page number", () => {
    expect(parseView("sessions?page=4").page).toBe(4);
  });

  it("rejects a non-numeric page", () => {
    expect(parseView("sessions?page=abc").page).toBe(1);
  });

  it("rejects a zero or negative page", () => {
    expect(parseView("sessions?page=0").page).toBe(1);
    expect(parseView("sessions?page=-3").page).toBe(1);
  });

  it("reads a persona list", () => {
    expect(parseView("overview?persona=sakthai,saksee").personas).toEqual(["sakthai", "saksee"]);
  });

  it("normalises persona case and whitespace", () => {
    expect(parseView("overview?persona=%20SakThai%20").personas).toEqual(["sakthai"]);
  });

  it("deduplicates personas", () => {
    expect(parseView("overview?persona=sakthai,sakthai").personas).toEqual(["sakthai"]);
  });

  it("treats an empty persona value as no filter", () => {
    expect(parseView("overview?persona=").personas).toEqual([]);
  });

  it("drops a persona name that is not one of the six", () => {
    // Keeping it would split the page against itself: the lists would show the
    // whole family (the server reads the value as "no filter") while the
    // overview dimmed every card against a name that matches none of them.
    expect(parseView("overview?persona=nobody").personas).toEqual([]);
  });

  it("keeps the known names from a mixed list", () => {
    expect(parseView("overview?persona=nobody,sakthai").personas).toEqual(["sakthai"]);
  });

  // A stale or mistyped fragment used to survive parsing, which split the page
  // against itself: the server ignores an unknown name and answers unfiltered,
  // while the client-side panels matched nothing.
  it("drops a persona name outside the known family", () => {
    expect(parseView("overview?persona=sakwho").personas).toEqual([]);
  });

  it("keeps the known personas when a list mixes known and unknown names", () => {
    expect(parseView("overview?persona=sakthai,sakwho,saksee").personas).toEqual([
      "sakthai",
      "saksee",
    ]);
  });

  it("reads the open session and run", () => {
    const view = parseView("sessions?session=abc&run=xyz");
    expect(view.session).toBe("abc");
    expect(view.run).toBe("xyz");
  });

  it("reads the demo flag only for the exact value", () => {
    expect(parseView("overview?demo=1").demo).toBe(true);
    expect(parseView("overview?demo=0").demo).toBe(false);
    expect(parseView("overview?demo=true").demo).toBe(false);
  });
});

describe("serializeView", () => {
  it("omits every field at its default", () => {
    expect(serializeView(DEFAULT_VIEW)).toBe("overview");
  });

  it("keeps a non-default section with no params", () => {
    expect(serializeView({ ...DEFAULT_VIEW, tab: "memory" })).toBe("memory");
  });

  it("writes the search text", () => {
    expect(serializeView({ ...DEFAULT_VIEW, search: "deploy" })).toBe("overview?q=deploy");
  });

  it("omits page 1", () => {
    expect(serializeView({ ...DEFAULT_VIEW, page: 1 })).toBe("overview");
  });

  it("writes a page past the first", () => {
    expect(serializeView({ ...DEFAULT_VIEW, page: 3 })).toBe("overview?page=3");
  });

  it("writes personas as a comma-separated list", () => {
    expect(serializeView({ ...DEFAULT_VIEW, personas: ["sakthai", "saksee"] })).toBe(
      "overview?persona=sakthai%2Csaksee",
    );
  });

  it("round-trips a fully populated view", () => {
    const view = {
      tab: "sessions" as const,
      search: "deploy the thing",
      severity: "high",
      page: 3,
      personas: ["sakthai", "saksee"],
      session: "1700000000_abc",
      run: "run-1",
      agent: "sakking",
      demo: true,
      trend: 7 as const,
    };
    expect(parseView(serializeView(view))).toEqual(view);
  });

  it("carries the open persona drawer in the URL", () => {
    expect(serializeView({ ...DEFAULT_VIEW, agent: "saksee" })).toBe("overview?agent=saksee");
    expect(parseView("overview?agent=saksee").agent).toBe("saksee");
  });

  it("drops an unknown persona from the drawer field rather than opening nothing", () => {
    // Same rule the filter follows: a name outside the six would open a drawer
    // with no persona behind it, which renders as a blank panel rather than as
    // the bad link it is.
    expect(parseView("overview?agent=sakwho").agent).toBeNull();
    expect(parseView("overview?agent=").agent).toBeNull();
  });

  it("normalises the drawer's persona name the way the filter is normalised", () => {
    expect(parseView("overview?agent=%20SakSee%20").agent).toBe("saksee");
  });

  it("omits the drawer field when nothing is open", () => {
    expect(serializeView({ ...DEFAULT_VIEW, agent: null })).toBe("overview");
  });

  it("round-trips search text containing a separator", () => {
    // `?`, `&` and `=` in the query have to survive the fragment encoding.
    const view = { ...DEFAULT_VIEW, search: "a=b&c?d" };
    expect(parseView(serializeView(view)).search).toBe("a=b&c?d");
  });

  it("keeps the trend window in the URL, so a link carries it", () => {
    expect(serializeView({ ...DEFAULT_VIEW, trend: 7 })).toBe("overview?trend=7");
    expect(parseView("analytics?trend=7").trend).toBe(7);
  });

  it("omits the default window rather than spelling it out", () => {
    expect(serializeView({ ...DEFAULT_VIEW, trend: 30 })).toBe("overview");
  });

  it("keeps the all-history window, which is not the default", () => {
    expect(parseView(serializeView({ ...DEFAULT_VIEW, trend: 0 })).trend).toBe(0);
  });

  it("falls back to the default for a window nobody offers", () => {
    expect(parseView("analytics?trend=9999").trend).toBe(30);
    expect(parseView("analytics?trend=abc").trend).toBe(30);
    expect(parseView("analytics?trend=-7").trend).toBe(30);
  });
});
