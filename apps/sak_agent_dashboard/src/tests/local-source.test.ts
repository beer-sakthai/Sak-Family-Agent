/**
 * The local filesystem source, against a real seeded runtime tree.
 *
 * These read actual files and a **real SQLite database** — no `fs` mocking, no
 * inline literals. That matters: `lib/db.ts` previously used CommonJS
 * `require()` inside an ESM module, which threw under Vitest and was swallowed
 * into a demo-data fallback, so its SQLite path had never run under test.
 * `test_reads_a_real_sqlite_shard` below fails if that regresses.
 *
 * The behaviour under test mirrors `sakthai/web/api.py`, and both are checked
 * against the same generated contract.
 */

import { afterEach, beforeEach, describe, expect, it } from "vitest";
import fs from "fs";
import path from "path";

import { LocalFsSource, clearSessionCache } from "@/lib/sources/local";
import { NOW, evalLine, makeHome, removeHome, seedHome, seedShard, sessionDoc } from "./fixtures";

let home: string;

beforeEach(() => {
  home = makeHome();
  clearSessionCache();
});

afterEach(() => {
  removeHome(home);
});

describe("LocalFsSource.getPersonas", () => {
  it("reports all six personas even on an empty runtime", async () => {
    const payload = await new LocalFsSource(home).getPersonas();
    expect(payload.personas).toHaveLength(6);
    expect(payload.personas.map((p) => p.name)).toContain("saktan");
  });

  it("marks a persona with no shard rather than omitting it", async () => {
    const payload = await new LocalFsSource(home).getPersonas();
    expect(payload.personas.every((p) => p.has_shard === false)).toBe(true);
  });

  it("puts a record with no persona in the unattributed bucket", async () => {
    seedHome(home);
    const payload = await new LocalFsSource(home).getPersonas();
    expect(payload.unattributed_runs).toBe(1);
  });

  it("attributes a record that carries a persona", async () => {
    seedHome(home);
    const payload = await new LocalFsSource(home).getPersonas();
    const sakthai = payload.personas.find((p) => p.name === "sakthai")!;
    expect(sakthai.runs).toBe(1);
    expect(sakthai.errors).toBe(1);
  });

  it("attributes a persona-scoped log by its location", async () => {
    seedHome(home);
    const payload = await new LocalFsSource(home).getPersonas();
    // The saksee log's record has no persona field; its directory is the fact.
    expect(payload.personas.find((p) => p.name === "saksee")!.runs).toBe(1);
  });

  it("reads a real SQLite shard", async () => {
    seedShard(
      path.join(home, "sakthai", "memory.db"),
      [{ kind: "note", key: null, value: "a fact" }],
      [{ summary: "an observation", weight: 1, confidence: 0.5 }],
    );
    const payload = await new LocalFsSource(home).getPersonas();
    const sakthai = payload.personas.find((p) => p.name === "sakthai")!;
    expect(sakthai.has_shard).toBe(true);
    expect(sakthai.fact_count).toBe(1);
    expect(sakthai.observation_count).toBe(1);
  });

  it("averages latency in milliseconds", async () => {
    seedHome(home);
    const payload = await new LocalFsSource(home).getPersonas();
    expect(payload.personas.find((p) => p.name === "sakthai")!.avg_latency_ms).toBe(500);
  });

  it("tracks the newest run timestamp", async () => {
    fs.writeFileSync(
      path.join(home, "eval.jsonl"),
      [
        evalLine({ persona: "sakthai", timestamp: NOW }),
        evalLine({ persona: "sakthai", timestamp: NOW + 500 }),
      ].join("\n") + "\n",
    );
    const payload = await new LocalFsSource(home).getPersonas();
    expect(payload.personas.find((p) => p.name === "sakthai")!.last_run_at).toBe(NOW + 500);
  });

  it("does not invent a seventh persona from an unknown name", async () => {
    fs.writeFileSync(path.join(home, "eval.jsonl"), evalLine({ persona: "sakwho" }) + "\n");
    const payload = await new LocalFsSource(home).getPersonas();
    expect(payload.personas).toHaveLength(6);
    expect(payload.unattributed_runs).toBe(1);
  });
});

describe("LocalFsSource.getMetrics", () => {
  it("returns zeroes on an empty runtime", async () => {
    const metrics = await new LocalFsSource(home).getMetrics();
    expect(metrics.total_runs).toBe(0);
    expect(metrics.trends).toEqual([]);
  });

  it("counts records from every root", async () => {
    seedHome(home);
    expect((await new LocalFsSource(home).getMetrics()).total_runs).toBe(3);
  });

  it("skips a torn JSON line rather than failing", async () => {
    fs.writeFileSync(path.join(home, "eval.jsonl"), evalLine() + "\n{ broken\n");
    expect((await new LocalFsSource(home).getMetrics()).total_runs).toBe(1);
  });

  it("computes an error rate", async () => {
    seedHome(home);
    expect((await new LocalFsSource(home).getMetrics()).error_rate).toBeCloseTo(1 / 3, 3);
  });

  it("totals tokens", async () => {
    seedHome(home);
    const { tokens } = await new LocalFsSource(home).getMetrics();
    expect(tokens.total_tokens).toBe(tokens.input_tokens + tokens.output_tokens);
  });

  it("builds a stop-reason histogram", async () => {
    seedHome(home);
    expect((await new LocalFsSource(home).getMetrics()).stop_reasons).toEqual({ end_turn: 3 });
  });

  it("groups trends by UTC day", async () => {
    fs.writeFileSync(
      path.join(home, "eval.jsonl"),
      [evalLine({ timestamp: NOW }), evalLine({ timestamp: NOW + 86_400 * 2 })].join("\n") + "\n",
    );
    const trends = (await new LocalFsSource(home).getMetrics()).trends;
    expect(trends).toHaveLength(2);
    expect(trends[0].date < trends[1].date).toBe(true);
  });

  it("labels a record with no model as unknown", async () => {
    fs.writeFileSync(
      path.join(home, "eval.jsonl"),
      JSON.stringify({ timestamp: NOW, stop_reason: "end_turn" }) + "\n",
    );
    expect((await new LocalFsSource(home).getMetrics()).per_model).toHaveProperty("unknown");
  });
});

describe("LocalFsSource.getSessions", () => {
  it("is empty on a fresh runtime", async () => {
    const payload = await new LocalFsSource(home).getSessions();
    expect(payload).toEqual({ sessions: [], total: 0, detail: null });
  });

  it("summarises a session", async () => {
    seedHome(home);
    const session = (await new LocalFsSource(home).getSessions()).sessions[0];
    expect(session.id).toBe(`${NOW}_abc`);
    expect(session.persona).toBe("sakthai");
    expect(session.message_count).toBe(2);
    expect(session.tool_call_count).toBe(1);
    expect(session.tokens.total_tokens).toBe(14);
  });

  it("leaves a session with no persona unattributed", async () => {
    fs.mkdirSync(path.join(home, "sessions"), { recursive: true });
    fs.writeFileSync(path.join(home, "sessions", `${NOW}_x.json`), sessionDoc());
    expect((await new LocalFsSource(home).getSessions()).sessions[0].persona).toBeNull();
  });

  it("attributes a persona-scoped session by its directory", async () => {
    fs.mkdirSync(path.join(home, "saksit", "sessions"), { recursive: true });
    fs.writeFileSync(path.join(home, "saksit", "sessions", `${NOW}_y.json`), sessionDoc());
    expect((await new LocalFsSource(home).getSessions()).sessions[0].persona).toBe("saksit");
  });

  it("orders newest first", async () => {
    fs.mkdirSync(path.join(home, "sessions"), { recursive: true });
    for (const stamp of [NOW, NOW + 10, NOW + 20]) {
      fs.writeFileSync(path.join(home, "sessions", `${stamp}_s.json`), sessionDoc());
    }
    clearSessionCache();
    const ids = (await new LocalFsSource(home).getSessions()).sessions.map((s) => s.id);
    expect(ids).toEqual([`${NOW + 20}_s`, `${NOW + 10}_s`, `${NOW}_s`]);
  });

  it("skips a corrupt session file", async () => {
    fs.mkdirSync(path.join(home, "sessions"), { recursive: true });
    fs.writeFileSync(path.join(home, "sessions", `${NOW}_bad.json`), "{{{");
    fs.writeFileSync(path.join(home, "sessions", `${NOW}_ok.json`), sessionDoc());
    clearSessionCache();
    expect((await new LocalFsSource(home).getSessions()).total).toBe(1);
  });

  it("filters on search across every term", async () => {
    fs.mkdirSync(path.join(home, "sessions"), { recursive: true });
    fs.writeFileSync(
      path.join(home, "sessions", `${NOW}_a.json`),
      sessionDoc({ task: "deploy the thing" }),
    );
    fs.writeFileSync(
      path.join(home, "sessions", `${NOW + 1}_b.json`),
      sessionDoc({ task: "write a report" }),
    );
    clearSessionCache();
    expect((await new LocalFsSource(home).getSessions({ search: "deploy" })).total).toBe(1);
  });

  it("paginates", async () => {
    fs.mkdirSync(path.join(home, "sessions"), { recursive: true });
    for (let i = 0; i < 5; i += 1) {
      fs.writeFileSync(path.join(home, "sessions", `${NOW + i}_s.json`), sessionDoc());
    }
    clearSessionCache();
    const page = await new LocalFsSource(home).getSessions({ limit: 2, offset: 2 });
    expect(page.total).toBe(5);
    expect(page.sessions).toHaveLength(2);
  });

  it("clamps a nonsense limit instead of returning nothing", async () => {
    seedHome(home);
    clearSessionCache();
    const source = new LocalFsSource(home);
    expect((await source.getSessions({ limit: -5 })).sessions).toHaveLength(1);
    expect((await source.getSessions({ limit: 10_000 })).sessions).toHaveLength(1);
  });
});

describe("LocalFsSource persona filter", () => {
  function seedTwoPersonaSessions(): void {
    fs.mkdirSync(path.join(home, "sessions"), { recursive: true });
    fs.writeFileSync(
      path.join(home, "sessions", `${NOW}_a.json`),
      sessionDoc({ persona: "sakthai" }),
    );
    fs.writeFileSync(
      path.join(home, "sessions", `${NOW + 10}_b.json`),
      sessionDoc({ persona: "saksee" }),
    );
    clearSessionCache();
  }

  it("narrows sessions to the named persona", async () => {
    seedTwoPersonaSessions();
    const payload = await new LocalFsSource(home).getSessions({ personas: ["sakthai"] });
    expect(payload.sessions.map((s) => s.persona)).toEqual(["sakthai"]);
  });

  it("counts the filtered set", async () => {
    seedTwoPersonaSessions();
    expect((await new LocalFsSource(home).getSessions({ personas: ["sakthai"] })).total).toBe(1);
  });

  it("drops unattributed sessions from a filtered view", async () => {
    fs.mkdirSync(path.join(home, "sessions"), { recursive: true });
    fs.writeFileSync(path.join(home, "sessions", `${NOW}_u.json`), sessionDoc());
    clearSessionCache();
    expect((await new LocalFsSource(home).getSessions({ personas: ["sakthai"] })).total).toBe(0);
  });

  it("applies the filter before the offset", async () => {
    fs.mkdirSync(path.join(home, "sessions"), { recursive: true });
    for (const [index, persona] of ["sakthai", "saksee", "sakthai", "saksee"].entries()) {
      fs.writeFileSync(
        path.join(home, "sessions", `${NOW + index}_p.json`),
        sessionDoc({ persona }),
      );
    }
    clearSessionCache();
    const page = await new LocalFsSource(home).getSessions({
      personas: ["sakthai"],
      limit: 1,
      offset: 1,
    });
    expect(page.total).toBe(2);
    expect(page.sessions[0].persona).toBe("sakthai");
  });

  it("combines with the search text", async () => {
    fs.mkdirSync(path.join(home, "sessions"), { recursive: true });
    fs.writeFileSync(
      path.join(home, "sessions", `${NOW}_s1.json`),
      sessionDoc({ persona: "sakthai", task: "deploy the thing" }),
    );
    fs.writeFileSync(
      path.join(home, "sessions", `${NOW + 1}_s2.json`),
      sessionDoc({ persona: "saksee", task: "deploy the thing" }),
    );
    clearSessionCache();
    const payload = await new LocalFsSource(home).getSessions({
      personas: ["sakthai"],
      search: "deploy",
    });
    expect(payload.total).toBe(1);
  });

  it("returns every persona when the filter is empty", async () => {
    seedTwoPersonaSessions();
    expect((await new LocalFsSource(home).getSessions({ personas: [] })).total).toBe(2);
  });

  it("narrows memory to the named persona's own shard", async () => {
    seedShard(path.join(home, "sakthai", "memory.db"), [
      { kind: "preference", key: "theme", value: "dark mode" },
    ]);
    seedShard(path.join(home, "saksee", "memory.db"), [
      { kind: "preference", key: "theme", value: "light mode" },
    ]);
    const payload = await new LocalFsSource(home).getMemory({ personas: ["sakthai"] });
    expect(payload.facts.map((f) => f.value)).toEqual(["dark mode"]);
  });

  it("narrows the memory totals, not only the rows", async () => {
    seedShard(path.join(home, "sakthai", "memory.db"), [
      { kind: "preference", key: "a", value: "one" },
    ]);
    seedShard(path.join(home, "saksee", "memory.db"), [
      { kind: "preference", key: "b", value: "two" },
    ]);
    const payload = await new LocalFsSource(home).getMemory({ personas: ["sakthai"] });
    expect(payload.total_facts).toBe(1);
  });

  it("excludes the unscoped shard from a filtered memory view", async () => {
    seedShard(path.join(home, "memory.db"), [
      { kind: "preference", key: "a", value: "unscoped" },
    ]);
    seedShard(path.join(home, "sakthai", "memory.db"), [
      { kind: "preference", key: "b", value: "scoped" },
    ]);
    const payload = await new LocalFsSource(home).getMemory({ personas: ["sakthai"] });
    expect(payload.facts.map((f) => f.value)).toEqual(["scoped"]);
    expect(payload.total_facts).toBe(1);
  });

  it("spans the family when memory is unfiltered", async () => {
    seedShard(path.join(home, "sakthai", "memory.db"), [
      { kind: "preference", key: "a", value: "one" },
    ]);
    seedShard(path.join(home, "saksee", "memory.db"), [
      { kind: "preference", key: "b", value: "two" },
    ]);
    expect((await new LocalFsSource(home).getMemory()).total_facts).toBe(2);
  });
});

describe("LocalFsSource.getSessionDetail", () => {
  it("flattens block content", async () => {
    seedHome(home);
    const detail = await new LocalFsSource(home).getSessionDetail(`${NOW}_abc`);
    expect(detail?.messages[0].content).toBe("hi");
    expect(detail?.messages[1].content).toBe("yo");
  });

  it("reduces tool calls to name and error", async () => {
    seedHome(home);
    const detail = await new LocalFsSource(home).getSessionDetail(`${NOW}_abc`);
    expect(detail?.tool_calls).toEqual([{ name: "recall", is_error: false }]);
  });

  it("returns null for an unknown id", async () => {
    seedHome(home);
    expect(await new LocalFsSource(home).getSessionDetail("9999_nope")).toBeNull();
  });

  it.each(["../../etc/passwd", "a/b", "..", "with space"])(
    "rejects the traversal id %s",
    async (bad) => {
      seedHome(home);
      expect(await new LocalFsSource(home).getSessionDetail(bad)).toBeNull();
    },
  );
});

describe("LocalFsSource.getMemory", () => {
  it("is empty on a fresh runtime", async () => {
    const memory = await new LocalFsSource(home).getMemory();
    expect(memory.facts).toEqual([]);
    expect(memory.total_facts).toBe(0);
  });

  it("reads facts out of a real shard", async () => {
    seedHome(home);
    const memory = await new LocalFsSource(home).getMemory();
    expect(memory.total_facts).toBe(1);
    expect(memory.facts[0].value).toBe("dark mode");
    expect(memory.facts[0].tags).toEqual(["ui"]);
  });

  it("tags each fact with the shard it came from", async () => {
    seedHome(home);
    expect((await new LocalFsSource(home).getMemory()).facts[0].persona).toBe("sakthai");
  });

  it("merges across shards", async () => {
    seedShard(path.join(home, "sakthai", "memory.db"), [
      { kind: "note", key: null, value: "from thai" },
    ]);
    seedShard(path.join(home, "saksee", "memory.db"), [
      { kind: "note", key: null, value: "from see" },
    ]);
    const memory = await new LocalFsSource(home).getMemory();
    expect(memory.total_facts).toBe(2);
    expect(new Set(memory.facts.map((f) => f.persona))).toEqual(new Set(["sakthai", "saksee"]));
  });

  it("populates a growth series", async () => {
    seedHome(home);
    const memory = await new LocalFsSource(home).getMemory();
    expect(memory.fact_growth.labels).toHaveLength(30);
    expect(memory.fact_growth.values).toHaveLength(30);
  });

  it("counts facts by kind", async () => {
    seedHome(home);
    expect((await new LocalFsSource(home).getMemory()).kind_counts).toEqual({ preference: 1 });
  });

  it("filters on a query", async () => {
    seedShard(path.join(home, "memory.db"), [
      { kind: "note", key: null, value: "likes coffee" },
      { kind: "note", key: null, value: "likes tea" },
    ]);
    expect((await new LocalFsSource(home).getMemory({ query: "coffee" })).facts).toHaveLength(1);
  });

  it("counts this week's facts", async () => {
    seedHome(home);
    expect((await new LocalFsSource(home).getMemory()).facts_this_week).toBe(1);
  });
});

describe("LocalFsSource.getAudit", () => {
  it("is empty on a fresh runtime", async () => {
    expect(await new LocalFsSource(home).getAudit()).toEqual({
      events: [],
      severity_counts: {},
      total: 0,
    });
  });

  it("reads events newest first", async () => {
    seedHome(home);
    const audit = await new LocalFsSource(home).getAudit();
    expect(audit.total).toBe(2);
    expect(audit.events[0].timestamp).toBeGreaterThan(audit.events[1].timestamp);
  });

  it("counts every severity regardless of the filter", async () => {
    seedHome(home);
    const audit = await new LocalFsSource(home).getAudit({ severity: "high" });
    expect(audit.total).toBe(1);
    expect(audit.severity_counts).toEqual({ high: 1, low: 1 });
  });

  it("matches severity case-insensitively", async () => {
    seedHome(home);
    expect((await new LocalFsSource(home).getAudit({ severity: "HIGH" })).total).toBe(1);
  });

  it("narrows an unknown severity to nothing", async () => {
    // The previous reader ignored an unrecognised filter and returned
    // everything, which silently misreported the log.
    seedHome(home);
    expect((await new LocalFsSource(home).getAudit({ severity: "bogus" })).total).toBe(0);
  });

  it("reads a persona-scoped audit log", async () => {
    fs.mkdirSync(path.join(home, "sakjules"), { recursive: true });
    fs.writeFileSync(
      path.join(home, "sakjules", "audit.log"),
      JSON.stringify({ timestamp: 1, severity: "high", message: "x" }) + "\n",
    );
    expect((await new LocalFsSource(home).getAudit()).total).toBe(1);
  });

  it("defaults a missing severity to low", async () => {
    fs.writeFileSync(
      path.join(home, "audit.log"),
      JSON.stringify({ timestamp: 1, message: "x" }) + "\n",
    );
    expect((await new LocalFsSource(home).getAudit()).events[0].severity).toBe("low");
  });
});

describe("LocalFsSource workflows", () => {
  it("is empty when no runs directory exists", async () => {
    expect(await new LocalFsSource(home).getWorkflows()).toEqual({ runs: [] });
  });

  it("summarises a run", async () => {
    seedHome(home);
    const run = (await new LocalFsSource(home).getWorkflows()).runs[0];
    expect(run.run_id).toBe("run-1");
    expect(run.workflow_name).toBe("nightly");
    expect(run.step_count).toBe(2);
    expect(run.failed_steps).toBe(1);
  });

  it("lowercases the uppercase status the framework writes", async () => {
    seedHome(home);
    expect((await new LocalFsSource(home).getWorkflows()).runs[0].status).toBe("completed");
  });

  it("computes duration from ISO stamps", async () => {
    seedHome(home);
    expect((await new LocalFsSource(home).getWorkflows()).runs[0].duration_seconds).toBe(30);
  });

  it("returns step detail", async () => {
    seedHome(home);
    const detail = await new LocalFsSource(home).getWorkflow("run-1");
    const publish = detail!.steps.find((s) => s.step_id === "publish")!;
    expect(publish.status).toBe("failed");
    expect(publish.error).toBe("boom");
    expect(publish.attempts).toBe(3);
  });

  it("rejects a traversal run id", async () => {
    seedHome(home);
    expect(await new LocalFsSource(home).getWorkflow("../../etc/passwd")).toBeNull();
  });
});
