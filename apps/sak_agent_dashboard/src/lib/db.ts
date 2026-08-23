import path from "path";
import os from "os";
import fs from "fs";
import { MemoryData, FactRecord, ObservationRecord } from "./types";

const SAKTHAI_DIR = process.env.SAKTHAI_DIR || path.join(os.homedir(), ".sakthai");
const DB_FILE = path.join(SAKTHAI_DIR, "memory.db");

export function getDemoMemoryData(): MemoryData {
  return {
    facts: [
      {
        id: 1,
        entity: "SakThai",
        fact: "Primary model initialized with v2 architecture",
        persona: "SakThai",
        createdAt: "2026-08-02T12:00:00Z",
      },
      {
        id: 2,
        entity: "SakKing",
        fact: "Math proof solver loaded and verified",
        persona: "SakKing",
        createdAt: "2026-08-02T11:45:00Z",
      },
      {
        id: 3,
        entity: "SakSee",
        fact: "Vision image parser cached and operational",
        persona: "SakSee",
        createdAt: "2026-08-02T11:30:00Z",
      },
      {
        id: 4,
        entity: "SakSit",
        fact: "Security boundary rules enforced for filesystem access",
        persona: "SakSit",
        createdAt: "2026-08-02T11:00:00Z",
      },
      {
        id: 5,
        entity: "SakJules",
        fact: "Async background worker queue initialized",
        persona: "SakJules",
        createdAt: "2026-08-02T10:30:00Z",
      },
    ],
    observations: [
      {
        id: 1,
        category: "eval",
        observation: "Benchmark 95% passed across test suites",
        timestamp: "2026-08-02T12:00:00Z",
      },
      {
        id: 2,
        category: "telemetry",
        observation: "Average latency stable at 388ms",
        timestamp: "2026-08-02T11:50:00Z",
      },
      {
        id: 3,
        category: "security",
        observation: "Zero unauthorized memory access attempts detected",
        timestamp: "2026-08-02T11:15:00Z",
      },
    ],
  };
}

export async function getMemoryData(demo?: boolean, query?: string): Promise<MemoryData> {
  let memory: MemoryData = { facts: [], observations: [] };

  if (demo || !fs.existsSync(DB_FILE)) {
    memory = getDemoMemoryData();
  } else {
    try {
      // Dynamic import/require for better-sqlite3
      const Database = require("better-sqlite3");
      const db = new Database(DB_FILE, { readonly: true, fileMustExist: true });

      let facts: FactRecord[] = [];
      try {
        const factRows = db.prepare("SELECT * FROM facts").all();
        facts = factRows.map((row: any) => {
          const entity = row.entity || row.key || row.kind || row.source_session || "SakThai";
          const fact = row.fact || row.value || row.summary || "";
          const persona = row.persona || row.source_session || entity;
          const rawTs = row.createdAt || row.created_at;
          const createdAt =
            typeof rawTs === "number"
              ? new Date(rawTs * 1000).toISOString()
              : typeof rawTs === "string"
              ? rawTs
              : new Date().toISOString();

          return {
            id: row.id,
            entity,
            fact,
            persona,
            createdAt,
          };
        });
      } catch {
        facts = [];
      }

      let observations: ObservationRecord[] = [];
      try {
        const obsRows = db.prepare("SELECT * FROM observations").all();
        observations = obsRows.map((row: any) => {
          const category = row.category || row.evidence_session_id || "general";
          const observation = row.observation || row.summary || "";
          const rawTs = row.timestamp || row.created_at;
          const timestamp =
            typeof rawTs === "number"
              ? new Date(rawTs * 1000).toISOString()
              : typeof rawTs === "string"
              ? rawTs
              : new Date().toISOString();

          return {
            id: row.id,
            category,
            observation,
            timestamp,
          };
        });
      } catch {
        observations = [];
      }

      db.close();

      if (facts.length === 0 && observations.length === 0) {
        memory = getDemoMemoryData();
      } else {
        memory = { facts, observations };
      }
    } catch {
      memory = getDemoMemoryData();
    }
  }

  if (query && query.trim().length > 0) {
    // Sanitize search query input
    const cleanQuery = query.replace(/[<>]/g, "").trim().toLowerCase();
    if (cleanQuery.length > 0) {
      memory = {
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

  return memory;
}
