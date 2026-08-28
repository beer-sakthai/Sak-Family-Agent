/**
 * The single demo dataset.
 *
 * Two properties matter. It must cover all six personas (the three rival demo
 * definitions this replaces covered five, on two different scales), and it must
 * be deterministic — a demo that renders differently on each call cannot be
 * asserted against, which is how `Math.random()` ended up in a chart.
 */

import { describe, expect, it } from "vitest";

import { PERSONA_NAMES } from "@/lib/contracts.generated";
import {
  demoAudit,
  demoMemory,
  demoMetrics,
  demoPersonas,
  demoSessions,
  demoWorkflows,
} from "@/lib/demo";
import { DemoSource } from "@/lib/sources/demo";

describe("determinism", () => {
  it.each([
    ["personas", demoPersonas],
    ["metrics", demoMetrics],
    ["sessions", demoSessions],
    ["memory", demoMemory],
    ["audit", demoAudit],
    ["workflows", demoWorkflows],
  ])("%s returns identical output on repeated calls", (_name, build) => {
    expect(JSON.stringify(build())).toBe(JSON.stringify(build()));
  });
});

describe("demoPersonas", () => {
  it("covers every persona in the contract", () => {
    expect(demoPersonas().personas.map((p) => p.name)).toEqual([...PERSONA_NAMES]);
  });

  it("includes an idle persona, which is a real state", () => {
    const idle = demoPersonas().personas.filter((p) => p.runs === 0);
    expect(idle.length).toBeGreaterThan(0);
    expect(idle[0].has_shard).toBe(false);
    expect(idle[0].last_run_at).toBeNull();
  });

  it("reports unattributed runs, as a live log would", () => {
    expect(demoPersonas().unattributed_runs).toBeGreaterThan(0);
  });

  it("gives every persona a display name and model", () => {
    for (const persona of demoPersonas().personas) {
      expect(persona.display_name).toMatch(/^Sak/);
      expect(persona.model.length).toBeGreaterThan(0);
    }
  });
});

describe("demoMetrics", () => {
  it("totals tokens consistently", () => {
    const { tokens } = demoMetrics();
    expect(tokens.total_tokens).toBe(tokens.input_tokens + tokens.output_tokens);
  });

  it("produces an ordered trend series", () => {
    const dates = demoMetrics().trends.map((t) => t.date);
    expect([...dates].sort()).toEqual(dates);
  });
});

describe("demoSessions", () => {
  it("includes unattributed sessions", () => {
    expect(demoSessions().sessions.some((s) => s.persona === null)).toBe(true);
  });

  it("filters on search", () => {
    const filtered = demoSessions({ search: "release notes" });
    expect(filtered.total).toBe(1);
  });

  it("paginates", () => {
    const page = demoSessions({ limit: 2, offset: 2 });
    expect(page.sessions).toHaveLength(2);
    expect(page.total).toBeGreaterThan(2);
  });
});

describe("demoMemory", () => {
  it("returns a 30-point growth series", () => {
    expect(demoMemory().fact_growth.labels).toHaveLength(30);
  });

  it("grows monotonically", () => {
    const values = demoMemory().fact_growth.values;
    expect([...values].sort((a, b) => a - b)).toEqual(values);
  });

  it("filters on query", () => {
    expect(demoMemory({ query: "cork" }).facts).toHaveLength(1);
  });
});

describe("persona filtering", () => {
  it("narrows sessions to the named personas", () => {
    const rows = demoSessions({ personas: ["sakthai"] }).sessions;
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.every((row) => row.persona === "sakthai")).toBe(true);
  });

  it("counts the filtered session set, not the whole one", () => {
    const all = demoSessions().total;
    const filtered = demoSessions({ personas: ["sakthai"] }).total;
    expect(filtered).toBeGreaterThan(0);
    expect(filtered).toBeLessThan(all);
  });

  it("excludes unattributed sessions from a filtered view", () => {
    // Every fourth demo session has no persona; a filter naming a persona
    // must not sweep those in.
    const rows = demoSessions({ personas: ["sakthai"] }).sessions;
    expect(rows.some((row) => row.persona === null)).toBe(false);
  });

  it("combines the persona filter with the search text", () => {
    const rows = demoSessions({ personas: ["sakthai"] }).sessions;
    const term = rows[0].task.split(" ")[0].toLowerCase();
    const searched = demoSessions({ personas: ["sakthai"], search: term }).sessions;
    expect(searched.every((row) => row.persona === "sakthai")).toBe(true);
  });

  it("returns every persona when the filter is empty", () => {
    expect(demoSessions({ personas: [] }).total).toBe(demoSessions().total);
  });

  it("narrows memory rows to the named personas", () => {
    const payload = demoMemory({ personas: ["sakthai"] });
    expect(payload.facts.every((fact) => fact.persona === "sakthai")).toBe(true);
  });

  it("scales the memory totals with the filter", () => {
    // The sample totals stand in for a larger store. Left unscaled they would
    // report the family's count above one persona's rows.
    const all = demoMemory().total_facts;
    const filtered = demoMemory({ personas: ["sakthai"] }).total_facts;
    expect(filtered).toBeGreaterThan(0);
    expect(filtered).toBeLessThan(all);
  });

  it("keeps the memory growth series integral under a filter", () => {
    const values = demoMemory({ personas: ["sakthai"] }).fact_growth.values;
    expect(values.every((value) => Number.isInteger(value))).toBe(true);
  });

  it("leaves memory totals whole when the filter is empty", () => {
    expect(demoMemory({ personas: [] }).total_facts).toBe(demoMemory().total_facts);
  });
});

describe("persona-scoped aggregates", () => {
  it("scales the metrics totals with the filter", () => {
    const all = demoMetrics().total_runs;
    const filtered = demoMetrics({ personas: ["sakthai"] }).total_runs;
    expect(filtered).toBeGreaterThan(0);
    expect(filtered).toBeLessThan(all);
  });

  it("leaves the metrics whole when the filter is empty", () => {
    expect(demoMetrics({ personas: [] }).total_runs).toBe(demoMetrics().total_runs);
  });

  it("keeps the mean latency a mean, not a total", () => {
    // Latency does not scale with how many personas are selected.
    const all = demoMetrics().trends[0].avg_latency_ms;
    expect(demoMetrics({ personas: ["sakthai"] }).trends[0].avg_latency_ms).toBe(all);
  });

  it("keeps the stop-reason histogram summing to the runs above it", () => {
    const payload = demoMetrics({ personas: ["sakthai"] });
    const stopped = Object.values(payload.stop_reasons).reduce((sum, n) => sum + n, 0);
    expect(stopped).toBeLessThanOrEqual(payload.total_runs);
  });

  it("never emits a negative stop-reason count", () => {
    // A small enough share would drive `end_turn` below zero unclamped.
    const payload = demoMetrics({ personas: ["saktan"] });
    expect(Object.values(payload.stop_reasons).every((n) => n >= 0)).toBe(true);
  });

  it("narrows audit events to the filtered personas", () => {
    const all = demoAudit().total;
    const filtered = demoAudit({ personas: ["sakking"] }).total;
    expect(filtered).toBeGreaterThan(0);
    expect(filtered).toBeLessThan(all);
  });

  it("counts severities over the filtered audit set", () => {
    const payload = demoAudit({ personas: ["sakking"] });
    const counted = Object.values(payload.severity_counts).reduce((sum, n) => sum + n, 0);
    expect(counted).toBe(payload.total);
  });

  it("returns every audit event when the filter is empty", () => {
    expect(demoAudit({ personas: [] }).total).toBe(demoAudit().total);
  });
});

describe("demoAudit", () => {
  it("counts every severity", () => {
    expect(Object.keys(demoAudit().severity_counts).length).toBeGreaterThan(1);
  });

  it("narrows an unknown severity to nothing", () => {
    expect(demoAudit({ severity: "bogus" }).total).toBe(0);
  });

  it("keeps unfiltered counts when filtering", () => {
    const filtered = demoAudit({ severity: "critical" });
    expect(filtered.total).toBe(1);
    expect(Object.keys(filtered.severity_counts).length).toBeGreaterThan(1);
  });
});

describe("DemoSource", () => {
  it("identifies itself as demo", () => {
    expect(new DemoSource().kind).toBe("demo");
  });

  it("resolves a workflow detail for a known run", async () => {
    const source = new DemoSource();
    const runs = (await source.getWorkflows()).runs;
    const detail = await source.getWorkflow(runs[0].run_id);
    expect(detail?.steps).toHaveLength(runs[0].step_count);
  });

  it("returns null for an unknown run", async () => {
    expect(await new DemoSource().getWorkflow("nope")).toBeNull();
  });
});
