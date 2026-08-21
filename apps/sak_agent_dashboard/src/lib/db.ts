import path from "path";
import os from "os";
import fs from "fs";
import {
  MemoryData,
  FactRecord,
  ObservationRecord,
  MemoryShardStatus,
  DataSource,
} from "./types";
import { PERSONAS, personaName } from "./personas";
import { getDemoMemoryData as demoMemory } from "./demoData";

const SAKTHAI_DIR = process.env.SAKTHAI_DIR || path.join(os.homedir(), ".sakthai");

/** The legacy unscoped database, kept for local dev shells and older installs. */
const LEGACY_DB_FILE = path.join(SAKTHAI_DIR, "memory.db");

/**
 * Every memory database this dashboard should read, in display order.
 *
 * Deployed personas each run with `SAKTHAI_HOME=$HOME/.sakthai/$AGENT`
 * (`infra/vm-agents/systemd/sakthai-telegram@.service`), so each writes to its own shard at
 * `~/.sakthai/<persona>/memory.db`. Reading only the unscoped `memory.db` — as
 * this module used to — means reading a database nobody writes to on the real
 * deployment, then falling back to demo data, which is why it never looked
 * broken.
 *
 * This mirrors `config.persona_memory_db_path()` and the merge that
 * `FamilyMemoryView` (`personas/sakthai/sakthai/memory/merged.py`) performs
 * behind `sakthai memory family`.
 */
function shardPaths(): Array<{ persona: string; file: string }> {
  return [
    ...PERSONAS.map((p) => ({
      persona: p.slug,
      file: path.join(SAKTHAI_DIR, p.slug, "memory.db"),
    })),
    { persona: "legacy", file: LEGACY_DB_FILE },
  ];
}

/** Re-exported from the shared, client-safe demo module. */
export { getDemoMemoryData } from "./demoData";

/**
 * Whether the native SQLite driver actually loaded, resolved once.
 *
 * `better-sqlite3` is an `optionalDependency` compiled against a specific Node
 * ABI, so a deployment can install cleanly and still not be able to read a
 * single byte of memory — the module is simply absent, or was built for a
 * different Node major than the runtime image. The app keeps serving in that
 * state, which is the dangerous part: every shard reports zero rows and the
 * dashboard looks merely idle rather than broken.
 *
 * Resolving it once, explicitly, lets callers tell "the driver is missing"
 * apart from "there is genuinely nothing stored yet".
 */
let _driverError: string | null | undefined;

/**
 * Run the probe once against an injectable loader.
 *
 * The loader is a parameter because `db.ts` reaches the driver through CJS
 * `require()`, which module-level mocking does not intercept — and a failure
 * path that cannot be tested is a failure path nobody has seen work.
 */
export function probeMemoryDriver(
  load: () => unknown = () => require("better-sqlite3")
): string | null {
  try {
    load();
    return null;
  } catch (err) {
    return (
      "better-sqlite3 (optionalDependency) failed to load, so no memory shard " +
      "can be read. It is a native module: check it was built during install " +
      "and that the runtime Node major matches the one it was built against. " +
      `Underlying error: ${err instanceof Error ? err.message : String(err)}`
    );
  }
}

export function memoryDriverError(): string | null {
  if (_driverError === undefined) {
    _driverError = probeMemoryDriver();
  }
  return _driverError;
}

/** Test seam: forget the cached driver probe. */
export function _resetMemoryDriverProbe(): void {
  _driverError = undefined;
}

function toIso(raw: unknown): string {
  if (typeof raw === "number") return new Date(raw * 1000).toISOString();
  if (typeof raw === "string") return raw;
  return new Date().toISOString();
}

import { serverMemoryCache } from "./memoryCache";

/**
 * Read one shard. Returns its rows plus a status describing what happened, so a
 * shard that exists but cannot be opened is reported rather than silently
 * folded into "no data".
 */
function readShard(
  persona: string,
  file: string
): { facts: FactRecord[]; observations: ObservationRecord[]; status: MemoryShardStatus } {
  const cached = serverMemoryCache.getShard(persona);
  if (cached) {
    return {
      facts: cached.facts,
      observations: cached.observations,
      status: cached.status,
    };
  }

  const start = Date.now();
  const base: MemoryShardStatus = {
    persona,
    path: file,
    exists: false,
    factCount: 0,
    observationCount: 0,
  };

  if (!fs.existsSync(file)) {
    const result = { facts: [], observations: [], status: base };
    serverMemoryCache.setShard(persona, result);
    return result;
  }
  base.exists = true;

  const label = persona === "legacy" ? "legacy" : personaName(persona);

  const driverError = memoryDriverError();
  if (driverError !== null) {
    // Distinguish "cannot read anything, ever" from "this shard is empty".
    base.error = driverError;
    const result = { facts: [], observations: [], status: base };
    serverMemoryCache.setShard(persona, result);
    return result;
  }

  try {
    // better-sqlite3 is an optionalDependency: a machine without a native build
    // still runs the app, it just cannot read memory.
    const Database = require("better-sqlite3");
    const db = new Database(file, { readonly: true, fileMustExist: true });

    let facts: FactRecord[] = [];
    try {
      const rows = db.prepare("SELECT * FROM facts").all();
      facts = rows.map((row: any, i: number) => ({
        id: row.id ?? `${persona}-f${i}`,
        entity: row.entity || row.key || row.kind || row.source_session || label,
        fact: row.fact || row.value || row.summary || "",
        // Attribute to the shard that held the row. The row's own persona
        // column wins if it has one, since a merged legacy DB can hold rows
        // from several personas.
        persona: row.persona || (persona === "legacy" ? row.source_session || label : label),
        createdAt: toIso(row.createdAt ?? row.created_at),
      }));
    } catch {
      facts = [];
    }

    let observations: ObservationRecord[] = [];
    try {
      const rows = db.prepare("SELECT * FROM observations").all();
      observations = rows.map((row: any, i: number) => ({
        id: row.id ?? `${persona}-o${i}`,
        category: row.category || row.evidence_session_id || "general",
        observation: row.observation || row.summary || "",
        timestamp: toIso(row.timestamp ?? row.created_at),
      }));
    } catch {
      observations = [];
    }

    db.close();

    base.factCount = facts.length;
    base.observationCount = observations.length;
    serverMemoryCache.recordLatency(Date.now() - start);
    const result = { facts, observations, status: base };
    serverMemoryCache.setShard(persona, result);
    return result;
  } catch (err) {
    base.error = err instanceof Error ? err.message : String(err);
    const result = { facts: [], observations: [], status: base };
    serverMemoryCache.setShard(persona, result);
    return result;
  }
}

export interface MemoryResult {
  memory: MemoryData;
  dataSource: DataSource;
}

export async function getMemoryData(
  demo?: boolean,
  query?: string
): Promise<MemoryResult> {
  let memory: MemoryData;
  let dataSource: DataSource;

  if (demo) {
    memory = demoMemory();
    dataSource = "demo";
  } else {
    const shards = shardPaths();
    const anyExists = shards.some((s) => fs.existsSync(s.file));

    if (!anyExists) {
      // No shard and no legacy DB. Say so rather than serving demo data as if
      // it were real.
      memory = { ...demoMemory(), shards: shards.map((s) => readShard(s.persona, s.file).status) };
      dataSource = "unavailable";
    } else {
      const facts: FactRecord[] = [];
      const observations: ObservationRecord[] = [];
      const statuses: MemoryShardStatus[] = [];

      for (const { persona, file } of shards) {
        const r = readShard(persona, file);
        facts.push(...r.facts);
        observations.push(...r.observations);
        statuses.push(r.status);
      }

      // Deduplicate across shards the way FamilyMemoryView does: identical
      // entity+fact pairs recorded by more than one persona collapse to one row.
      const seenFacts = new Set<string>();
      const dedupedFacts = facts.filter((f) => {
        const k = `${f.entity}\u0000${f.fact}`;
        if (seenFacts.has(k)) return false;
        seenFacts.add(k);
        return true;
      });
      const seenObs = new Set<string>();
      const dedupedObs = observations.filter((o) => {
        const k = `${o.category}\u0000${o.observation}`;
        if (seenObs.has(k)) return false;
        seenObs.add(k);
        return true;
      });

      if (dedupedFacts.length === 0 && dedupedObs.length === 0) {
        // Shards exist but hold nothing readable. That is a live, empty read —
        // not a reason to show fabricated rows.
        memory = {
          facts: [],
          observations: [],
          shards: statuses,
          cacheMetrics: serverMemoryCache.getMetrics(),
        };
      } else {
        memory = {
          facts: dedupedFacts,
          observations: dedupedObs,
          shards: statuses,
          cacheMetrics: serverMemoryCache.getMetrics(),
        };
      }
      dataSource = "live";
    }
  }

  if (query && query.trim().length > 0) {
    // Sanitize search query input
    const cleanQuery = query.replace(/[<>]/g, "").trim().toLowerCase();
    if (cleanQuery.length > 0) {
      memory = {
        ...memory,
        facts: memory.facts.filter((f) => {
          const inEntity = (f.entity || "").toLowerCase().includes(cleanQuery);
          const inFact = (f.fact || "").toLowerCase().includes(cleanQuery);
          const inPersona = (f.persona || "").toLowerCase().includes(cleanQuery);
          return inEntity || inFact || inPersona;
        }),
        observations: memory.observations.filter((o) => {
          const inCat = (o.category || "").toLowerCase().includes(cleanQuery);
          const inObs = (o.observation || "").toLowerCase().includes(cleanQuery);
          return inCat || inObs;
        }),
      };
    }
  }

  return { memory, dataSource };
}
