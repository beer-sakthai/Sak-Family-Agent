import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import fs from "fs";
import os from "os";
import path from "path";

import {
  PERSONAS,
  PERSONA_COUNT,
  UNATTRIBUTED,
  personaBySlug,
  personaIndex,
  personaName,
  resolvePersonaSlug,
} from "@/lib/personas";

/**
 * Regression tests for the persona-attribution and data-source bugs.
 *
 * The behaviour under test is specifically that unattributable runs are NOT
 * silently assigned to a persona, and that a missing source file is reported as
 * `unavailable` rather than served as demo data that reads like a measurement.
 */

describe("persona roster", () => {
  it("carries all six personas from config.PERSONA_NAMES", () => {
    expect(PERSONA_COUNT).toBe(6);
    expect(PERSONAS.map((p) => p.slug)).toEqual([
      "sakthai",
      "sakking",
      "saksee",
      "saksit",
      "sakjules",
      "saktan",
    ]);
  });

  it("includes SakTan, which the dashboard previously omitted entirely", () => {
    const saktan = personaBySlug("saktan");
    expect(saktan).toBeDefined();
    expect(saktan!.name).toBe("SakTan");
    expect(saktan!.provider).toBe("ollama");
  });

  it("has no duplicate slugs or names", () => {
    expect(new Set(PERSONAS.map((p) => p.slug)).size).toBe(PERSONA_COUNT);
    expect(new Set(PERSONAS.map((p) => p.name)).size).toBe(PERSONA_COUNT);
  });

  it("resolves slug lookups and indexes case-insensitively", () => {
    expect(personaIndex("SakThai")).toBe(0);
    expect(personaName("saktan")).toBe("SakTan");
    expect(personaBySlug("SAKJULES")?.name).toBe("SakJules");
    expect(personaIndex("nobody")).toBe(-1);
  });
});

describe("resolvePersonaSlug", () => {
  it("resolves an exact slug", () => {
    expect(resolvePersonaSlug({ persona: "sakthai" })).toBe("sakthai");
  });

  it("resolves a slug embedded in a longer label", () => {
    expect(resolvePersonaSlug({ persona: "SakSee · Web Specialist" })).toBe("saksee");
    expect(resolvePersonaSlug({ persona: "saktan_agent_bot" })).toBe("saktan");
  });

  it("falls back to the agent field", () => {
    expect(resolvePersonaSlug({ agent: "sakking" })).toBe("sakking");
  });

  it("returns null rather than guessing when there is no persona field", () => {
    // This is the core of the fix: the old code returned `index % 5` here, so
    // an unattributed run was counted against whichever persona its line
    // position happened to land on.
    expect(resolvePersonaSlug({})).toBeNull();
    expect(resolvePersonaSlug({ persona: "" })).toBeNull();
    expect(resolvePersonaSlug({ persona: "   " })).toBeNull();
    expect(resolvePersonaSlug({ persona: 42 })).toBeNull();
    expect(resolvePersonaSlug({ persona: "someone-else" })).toBeNull();
  });

  it("does not infer a persona from a model name", () => {
    // SakThai and SakSee share gemini-3.1-flash-lite, so a model name cannot
    // identify a persona. The old heuristic mapped gemini -> SakSee outright.
    expect(resolvePersonaSlug({ model: "gemini-3.1-flash-lite" } as never)).toBeNull();
    expect(resolvePersonaSlug({ model: "claude-opus-4-8" } as never)).toBeNull();
  });
});

describe("eval aggregation attribution and data source", () => {
  let tmp: string;

  beforeEach(() => {
    tmp = fs.mkdtempSync(path.join(os.tmpdir(), "sak-dash-"));
    process.env.SAKTHAI_DIR = tmp;
    vi.resetModules();
  });

  afterEach(() => {
    delete process.env.SAKTHAI_DIR;
    fs.rmSync(tmp, { recursive: true, force: true });
    vi.resetModules();
  });

  async function loadLib() {
    return await import("@/lib/sakthai");
  }

  function writeEval(lines: object[]) {
    fs.writeFileSync(
      path.join(tmp, "eval.jsonl"),
      lines.map((l) => JSON.stringify(l)).join("\n") + "\n",
      "utf8"
    );
  }

  it("reports 'unavailable' when eval.jsonl does not exist", async () => {
    const { getAgentOverview, getMetricsSummary } = await loadLib();
    const agents = await getAgentOverview();
    expect(agents.dataSource).toBe("unavailable");
    expect(agents.unattributedRuns).toBe(0);

    const metrics = await getMetricsSummary();
    expect(metrics.dataSource).toBe("unavailable");
  });

  it("reports 'demo' when demo mode is requested", async () => {
    const { getAgentOverview } = await loadLib();
    const r = await getAgentOverview(true);
    expect(r.dataSource).toBe("demo");
    expect(r.agents).toHaveLength(PERSONA_COUNT);
  });

  it("attributes runs only via an explicit persona field", async () => {
    writeEval([
      { persona: "sakthai", latency_s: 1.0 },
      { persona: "sakthai", latency_s: 2.0 },
      { persona: "saktan", latency_s: 0.5 },
    ]);
    const { getAgentOverview } = await loadLib();
    const { agents, dataSource, unattributedRuns } = await getAgentOverview();

    expect(dataSource).toBe("live");
    expect(unattributedRuns).toBe(0);

    const byName = Object.fromEntries(agents.map((a) => [a.name, a]));
    expect(byName.SakThai.runs).toBe(2);
    expect(byName.SakThai.latencyMs).toBe(1500);
    expect(byName.SakTan.runs).toBe(1);
    expect(byName.SakTan.latencyMs).toBe(500);
    // Personas with no runs report zero, not a borrowed share of someone else's.
    expect(byName.SakKing.runs).toBe(0);
    expect(byName.SakSee.runs).toBe(0);
  });

  it("routes unattributable runs to a visible bucket instead of a persona", async () => {
    writeEval([
      { latency_s: 1.0 },
      { latency_s: 1.0 },
      { latency_s: 1.0 },
      { persona: "sakthai", latency_s: 2.0 },
    ]);
    const { getAgentOverview } = await loadLib();
    const { agents, unattributedRuns } = await getAgentOverview();

    expect(unattributedRuns).toBe(3);

    // The three unattributed runs must not appear against any real persona.
    const rosterRuns = agents
      .filter((a) => !a.unattributed)
      .reduce((sum, a) => sum + a.runs, 0);
    expect(rosterRuns).toBe(1);

    const bucket = agents.find((a) => a.unattributed);
    expect(bucket).toBeDefined();
    expect(bucket!.slug).toBe(UNATTRIBUTED);
    expect(bucket!.runs).toBe(3);
    expect(bucket!.latencyMs).toBe(1000);
  });

  it("omits the unattributed bucket when every run is attributed", async () => {
    writeEval([{ persona: "sakjules", latency_s: 0.2 }]);
    const { getAgentOverview } = await loadLib();
    const { agents } = await getAgentOverview();
    expect(agents.find((a) => a.unattributed)).toBeUndefined();
    expect(agents).toHaveLength(PERSONA_COUNT);
  });

  it("does not report a fabricated benchmark score on live data", async () => {
    writeEval([{ persona: "sakthai", latency_s: 1.0 }]);
    const { getAgentOverview } = await loadLib();
    const { agents } = await getAgentOverview();
    // eval.jsonl carries no benchmark; the old code spread a hard-coded score
    // into the live path where it read as measured.
    expect(agents.every((a) => a.benchmarkScore === undefined)).toBe(true);
  });

  it("skips corrupt lines without shifting attribution", async () => {
    fs.writeFileSync(
      path.join(tmp, "eval.jsonl"),
      ['{"persona":"sakthai","latency_s":1.0}', "{ not json", '{"persona":"sakthai","latency_s":1.0}'].join(
        "\n"
      ),
      "utf8"
    );
    const { getAgentOverview } = await loadLib();
    const { agents, unattributedRuns } = await getAgentOverview();
    const sakthai = agents.find((a) => a.name === "SakThai")!;
    expect(sakthai.runs).toBe(2);
    expect(unattributedRuns).toBe(0);
  });

  it("reports an existing but empty eval.jsonl as a live read of zero", async () => {
    // An empty file is a real measurement of zero runs; only a *missing* file
    // is `unavailable`. Neither renders demo numbers as if they were measured.
    fs.writeFileSync(path.join(tmp, "eval.jsonl"), "", "utf8");
    const { getMetricsSummary, getAgentOverview } = await loadLib();

    const { metrics, dataSource } = await getMetricsSummary();
    expect(dataSource).toBe("live");
    expect(metrics.totalRuns).toBe(0);
    expect(metrics.trends).toEqual([]);

    const overview = await getAgentOverview();
    expect(overview.dataSource).toBe("live");
    expect(overview.agents).toHaveLength(PERSONA_COUNT);
    expect(overview.agents.every((a) => a.runs === 0)).toBe(true);
    expect(overview.agents.every((a) => a.status === "Idle")).toBe(true);
  });
});

describe("memory shard discovery", () => {
  let tmp: string;

  beforeEach(() => {
    tmp = fs.mkdtempSync(path.join(os.tmpdir(), "sak-mem-"));
    process.env.SAKTHAI_DIR = tmp;
    vi.resetModules();
  });

  afterEach(() => {
    delete process.env.SAKTHAI_DIR;
    fs.rmSync(tmp, { recursive: true, force: true });
    vi.resetModules();
  });

  it("reports 'unavailable' when neither a shard nor the legacy db exists", async () => {
    const { getMemoryData } = await import("@/lib/db");
    const { dataSource } = await getMemoryData();
    expect(dataSource).toBe("unavailable");
  });

  it("looks for a per-persona shard for every persona plus the legacy db", async () => {
    const { getMemoryData } = await import("@/lib/db");
    const { memory } = await getMemoryData();
    const shards = memory.shards ?? [];
    // Deployed personas write to ~/.sakthai/<persona>/memory.db, not the
    // unscoped file the dashboard used to read exclusively.
    expect(shards).toHaveLength(PERSONA_COUNT + 1);
    for (const p of PERSONAS) {
      const shard = shards.find((s) => s.persona === p.slug);
      expect(shard, `missing shard entry for ${p.slug}`).toBeDefined();
      expect(shard!.path).toBe(path.join(tmp, p.slug, "memory.db"));
    }
    expect(shards.find((s) => s.persona === "legacy")!.path).toBe(
      path.join(tmp, "memory.db")
    );
  });

  it("returns demo data in demo mode", async () => {
    const { getMemoryData } = await import("@/lib/db");
    const { memory, dataSource } = await getMemoryData(true);
    expect(dataSource).toBe("demo");
    expect(memory.facts.length).toBeGreaterThan(0);
  });
});
