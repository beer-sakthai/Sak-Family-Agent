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
import { DataSourceStrategy, SourceUnavailableError, resolveDataSource } from "./dataSource";

const SAKTHAI_DIR = process.env.SAKTHAI_DIR || path.join(os.homedir(), ".sakthai");

/** The legacy unscoped database, kept for local dev shells and older installs. */
const LEGACY_DB_FILE = path.join(SAKTHAI_DIR, "memory.db");

/**
 * Every memory database this dashboard should read, in display order.
 *
 * Deployed personas each run with `SAKTHAI_HOME=$HOME/.sakthai/$AGENT`
 * (`infra/vm-agents/sakthai-agent-run.sh`), so each writes to its own shard at
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
  const strategy: DataSourceStrategy<MemoryData> = {
    readDemo: () => demoMemory(),

    readLive: async () => {
      const shards = shardPaths();
      const anyExists = shards.some((s) => fs.existsSync(s.file));

      if (!anyExists) {
        // No shard and no legacy DB. Say so rather than serving demo data as
        // if it were real — but still attach the real (all-absent) per-shard
        // status list, which plain demo data does not carry, so the UI can
        // show exactly which personas were checked.
        throw new SourceUnavailableError(
          "No memory shard or legacy database found",
          {
            ...demoMemory(),
            shards: shards.map((s) => readShard(s.persona, s.file).status),
          }
        );
      }

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

      // Shards exist but may hold nothing readable — that is still a live,
      // empty read, not a reason to show fabricated rows. (Same shape either
      // way; kept as two branches to mirror the pre-Strategy code exactly.)
      if (dedupedFacts.length === 0 && dedupedObs.length === 0) {
        return {
          facts: [],
          observations: [],
          shards: statuses,
          cacheMetrics: serverMemoryCache.getMetrics(),
        };
      }
      return {
        facts: dedupedFacts,
        observations: dedupedObs,
        shards: statuses,
        cacheMetrics: serverMemoryCache.getMetrics(),
      };
    },
  };

  const { data, dataSource } = await resolveDataSource(strategy, !!demo);
  let memory = data;

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
