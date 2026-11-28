import fs from "fs";
import os from "os";
import path from "path";
import { NextRequest, NextResponse } from "next/server";
import { openWritableDb } from "@/lib/db";

export const runtime = "nodejs";

const DEFAULT_GATEWAY_URL = "http://127.0.0.1:8080";
const MAX_MEMORY_CONTENT_CHARS = 4000;

function redactSecrets(text: string): string {
  return text
    .replace(/\b(sk-[a-zA-Z0-9_-]{20,})\b/g, "[REDACTED_API_KEY]")
    .replace(/\b(ghp_[a-zA-Z0-9]{20,})\b/g, "[REDACTED_TOKEN]")
    .replace(/\b(hf_[a-zA-Z0-9]{20,})\b/g, "[REDACTED_HF_TOKEN]");
}

function getGatewayConfig() {
  const baseUrl = (
    process.env.SAKTHAI_GATEWAY_URL ||
    process.env.NEXT_PUBLIC_GATEWAY_URL ||
    DEFAULT_GATEWAY_URL
  ).replace(/\/$/, "");
  const token =
    process.env.SAKTHAI_GATEWAY_TOKEN ||
    process.env.SAKTHAI_API_TOKEN ||
    process.env.SAKTHAI_GATEWAY_BEARER_TOKEN ||
    "";
  return { baseUrl, token };
}

export async function POST(request: NextRequest) {
  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { ok: false, error: "Invalid JSON in request body" },
      { status: 400 }
    );
  }

  const id = Number(body.id);
  if (!Number.isFinite(id) || id <= 0) {
    return NextResponse.json(
      { ok: false, error: "Valid numeric fact 'id' is required" },
      { status: 400 }
    );
  }

  const rawValue = body.value;
  if (typeof rawValue !== "string" || !rawValue.trim()) {
    return NextResponse.json(
      { ok: false, error: "Non-empty string 'value' is required" },
      { status: 400 }
    );
  }

  const persona = typeof body.persona === "string" ? body.persona.trim().toLowerCase() : "sakthai";
  const cleanValue = redactSecrets(rawValue.trim()).slice(0, MAX_MEMORY_CONTENT_CHARS);
  const cleanKey =
    body.key !== undefined
      ? (typeof body.key === "string" && body.key.trim() ? redactSecrets(body.key.trim()) : null)
      : undefined;
  const cleanKind = typeof body.kind === "string" && body.kind.trim() ? body.kind.trim().toLowerCase() : undefined;
  const cleanTags: string[] | undefined = Array.isArray(body.tags)
    ? body.tags.map((t) => redactSecrets(String(t).trim())).filter(Boolean)
    : undefined;

  // 1. Attempt to proxy to Gateway daemon if reachable
  const { baseUrl, token } = getGatewayConfig();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const res = await fetch(`${baseUrl}/v1/memory/facts/edit`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        id,
        persona,
        value: cleanValue,
        key: cleanKey,
        kind: cleanKind,
        tags: cleanTags,
      }),
      signal: AbortSignal.timeout(1500),
    });

    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data, { status: res.status });
    }
  } catch {
    // Gateway offline or endpoint unavailable: gracefully fall back to direct SQLite shard mutation
  }

  // 2. Direct SQLite shard mutation fallback
  try {
    const home = process.env.SAKTHAI_HOME || path.join(os.homedir(), ".sakthai");
    let shardFile = path.join(home, persona, "memory.db");

    if (!fs.existsSync(shardFile)) {
      const sharedShard = path.join(home, "memory.db");
      if (fs.existsSync(sharedShard)) {
        shardFile = sharedShard;
      } else {
        return NextResponse.json(
          { ok: false, status: "not_found", error: `Memory shard not found for persona '${persona}'` },
          { status: 404 }
        );
      }
    }

    const mutationResult = openWritableDb(shardFile, (db) => {
      const existing = db.prepare("SELECT * FROM facts WHERE id = ?").get(id);
      if (!existing) {
        return { notFound: true, updatedRow: null };
      }

      const now = Math.floor(Date.now() / 1000);
      const targetKey = cleanKey !== undefined ? cleanKey : existing.key;
      const targetKind = cleanKind !== undefined ? cleanKind : (existing.kind || "note");
      const targetTags = cleanTags !== undefined ? JSON.stringify(cleanTags) : (existing.tags || "[]");

      const updateResult = db.prepare(
        "UPDATE facts SET value = ?, key = ?, kind = ?, tags = ?, updated_at = ? WHERE id = ?"
      ).run(cleanValue, targetKey, targetKind, targetTags, now, id);

      if (updateResult.changes === 0) {
        return { notFound: true, updatedRow: null };
      }

      const updatedRow = db.prepare("SELECT * FROM facts WHERE id = ?").get(id);
      return { notFound: false, updatedRow };
    });

    if (!mutationResult || mutationResult.notFound || !mutationResult.updatedRow) {
      return NextResponse.json(
        { ok: false, status: "not_found", error: `Fact with ID ${id} not found in ${persona} shard` },
        { status: 404 }
      );
    }

    const r = mutationResult.updatedRow;
    let finalTags: string[] = [];
    try {
      if (typeof r.tags === "string") {
        const parsed = JSON.parse(r.tags);
        if (Array.isArray(parsed)) finalTags = parsed.map(String);
      }
    } catch {
      finalTags = [];
    }

    return NextResponse.json({
      ok: true,
      status: "success",
      source: "sqlite_direct",
      fact: {
        id: Number(r.id),
        persona,
        kind: String(r.kind || "note"),
        key: r.key ? String(r.key) : null,
        value: String(r.value),
        tags: finalTags,
        updated_at: Number(r.updated_at),
        created_at: Number(r.created_at || r.updated_at),
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { ok: false, status: "error", error: message },
      { status: 500 }
    );
  }
}
