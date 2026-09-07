/**
 * Builds a real `~/.sakthai`-shaped tree on disk for tests to read.
 *
 * Deliberately writes actual files — including a **real SQLite database** via
 * better-sqlite3 — rather than mocking `fs`. The previous suite mocked nothing
 * and asserted against inline literals when an import failed, which meant the
 * SQLite read path had never executed under test even once. A fixture on a
 * temp directory costs milliseconds and exercises the code that ships.
 */

import Database from "better-sqlite3";
import fs from "fs";
import os from "os";
import path from "path";

export const NOW = 1_787_000_000;

export interface EvalOverrides {
  timestamp?: number;
  model?: string;
  provider?: string;
  stop_reason?: string;
  latency_s?: number;
  input_tokens?: number;
  output_tokens?: number;
  had_error?: boolean;
  persona?: string | null;
}

export function evalLine(overrides: EvalOverrides = {}): string {
  return JSON.stringify({
    timestamp: NOW,
    task_preview: "a task",
    model: "m1",
    provider: "anthropic",
    iterations: 1,
    stop_reason: "end_turn",
    latency_s: 1.0,
    input_tokens: 10,
    output_tokens: 4,
    tool_call_count: 0,
    had_error: false,
    ...overrides,
  });
}

export function sessionDoc(overrides: Record<string, unknown> = {}): string {
  return JSON.stringify({
    timestamp: NOW,
    task: "do the thing",
    model: "m1",
    persona: null,
    messages: [
      { role: "user", content: "hi" },
      { role: "assistant", content: [{ type: "text", text: "yo" }] },
    ],
    usage: { input_tokens: 10, output_tokens: 4, total_tokens: 14 },
    result: {
      text: "done",
      iterations: 1,
      stop_reason: "end_turn",
      tool_calls: [{ name: "recall", input: {}, is_error: false }],
    },
    ...overrides,
  });
}

/** Create an empty temp runtime root. Caller removes it. */
export function makeHome(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), "sakthai-fixture-"));
}

export function removeHome(home: string): void {
  fs.rmSync(home, { recursive: true, force: true });
}

/** Write a memory shard with the real schema `MemoryStore` creates. */
export function seedShard(
  file: string,
  facts: { kind: string; key: string | null; value: string; tags?: string[] }[] = [],
  observations: { summary: string; weight: number; confidence: number }[] = [],
): void {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const db = new Database(file);
  db.exec(`
    CREATE TABLE IF NOT EXISTS facts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      kind TEXT NOT NULL DEFAULT 'note',
      key TEXT,
      value TEXT NOT NULL,
      source_session TEXT,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL,
      tags TEXT
    );
    CREATE TABLE IF NOT EXISTS observations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      summary TEXT NOT NULL,
      evidence_session_id TEXT,
      weight REAL NOT NULL DEFAULT 1.0,
      confidence REAL NOT NULL DEFAULT 0.5,
      created_at INTEGER NOT NULL
    );
  `);

  // Recent, so the "this week" and growth-bin branches are actually exercised.
  const now = Math.floor(Date.now() / 1000);
  const insertFact = db.prepare(
    "INSERT INTO facts (kind, key, value, created_at, updated_at, tags) VALUES (?, ?, ?, ?, ?, ?)",
  );
  for (const fact of facts) {
    insertFact.run(fact.kind, fact.key, fact.value, now, now, JSON.stringify(fact.tags ?? []));
  }
  const insertObs = db.prepare(
    "INSERT INTO observations (summary, weight, confidence, created_at) VALUES (?, ?, ?, ?)",
  );
  for (const obs of observations) {
    insertObs.run(obs.summary, obs.weight, obs.confidence, now);
  }
  db.close();
}

/**
 * A populated runtime root:
 *   - one legacy eval record with no persona, one attributed to sakthai
 *   - a saksee-scoped eval log whose records carry no persona field
 *   - one session, one audit log, one memory shard, one workflow run
 */
export function seedHome(home: string): string {
  fs.mkdirSync(path.join(home, "sessions"), { recursive: true });
  fs.writeFileSync(
    path.join(home, "eval.jsonl"),
    [
      evalLine(),
      evalLine({ persona: "sakthai", model: "m2", had_error: true, latency_s: 0.5 }),
      "{ not json",
    ].join("\n") + "\n",
  );

  fs.mkdirSync(path.join(home, "saksee"), { recursive: true });
  fs.writeFileSync(path.join(home, "saksee", "eval.jsonl"), evalLine({ latency_s: 2.0 }) + "\n");

  fs.writeFileSync(
    path.join(home, "sessions", `${NOW}_abc.json`),
    sessionDoc({ persona: "sakthai" }),
  );

  fs.writeFileSync(
    path.join(home, "audit.log"),
    [
      JSON.stringify({
        timestamp: NOW,
        type: "mcp_validation",
        severity: "high",
        message: "blocked",
        details: { server: "x" },
      }),
      JSON.stringify({
        timestamp: NOW - 50,
        type: "env_pin",
        severity: "low",
        message: "ok",
        details: {},
      }),
    ].join("\n") + "\n",
  );

  seedShard(
    path.join(home, "sakthai", "memory.db"),
    [{ kind: "preference", key: "theme", value: "dark mode", tags: ["ui"] }],
    [{ summary: "works late", weight: 2.0, confidence: 0.9 }],
  );

  fs.mkdirSync(path.join(home, "workflow_runs"), { recursive: true });
  fs.writeFileSync(
    path.join(home, "workflow_runs", "run-1.json"),
    JSON.stringify({
      run_id: "run-1",
      workflow_name: "nightly",
      // Uppercase, as agent_workflow's RunStatus actually serialises.
      status: "COMPLETED",
      start_time: "2026-08-26T10:00:00",
      end_time: "2026-08-26T10:00:30",
      step_results: {
        fetch: {
          step_id: "fetch",
          status: "COMPLETED",
          output: {},
          error: null,
          attempts: 1,
          start_time: "2026-08-26T10:00:00",
          end_time: "2026-08-26T10:00:10",
        },
        publish: {
          step_id: "publish",
          status: "FAILED",
          output: {},
          error: "boom",
          attempts: 3,
          start_time: "2026-08-26T10:00:10",
          end_time: "2026-08-26T10:00:30",
        },
      },
    }),
  );

  return home;
}
