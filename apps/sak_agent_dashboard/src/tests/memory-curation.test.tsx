import React from "react";
import fs from "fs";
import os from "os";
import path from "path";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import Database from "better-sqlite3";

import { POST as editPOST } from "@/app/api/gateway/memory/edit/route";
import { MemoryExplorer } from "@/components/MemoryExplorer";
import { NextRequest } from "next/server";
import type { MemoryPayload } from "@/lib/contracts.generated";

describe("Memory Curation API: POST /api/gateway/memory/edit", () => {
  it("rejects invalid JSON with 400", async () => {
    const req = new NextRequest("http://localhost:3000/api/gateway/memory/edit", {
      method: "POST",
      body: "not-json{",
    });
    const res = await editPOST(req);
    expect(res.status).toBe(400);
    const json = await res.json();
    expect(json.ok).toBe(false);
    expect(json.error).toMatch(/Invalid JSON/);
  });

  it("rejects missing or non-positive fact id with 400", async () => {
    const req = new NextRequest("http://localhost:3000/api/gateway/memory/edit", {
      method: "POST",
      body: JSON.stringify({ id: 0, value: "hello" }),
    });
    const res = await editPOST(req);
    expect(res.status).toBe(400);
    const json = await res.json();
    expect(json.ok).toBe(false);
    expect(json.error).toMatch(/fact 'id' is required/);
  });

  it("rejects empty or whitespace value with 400", async () => {
    const req = new NextRequest("http://localhost:3000/api/gateway/memory/edit", {
      method: "POST",
      body: JSON.stringify({ id: 1, value: "   " }),
    });
    const res = await editPOST(req);
    expect(res.status).toBe(400);
    const json = await res.json();
    expect(json.ok).toBe(false);
    expect(json.error).toMatch(/Non-empty string 'value'/);
  });

  it("returns 404 when memory shard does not exist", async () => {
    const prevHome = process.env.SAKTHAI_HOME;
    process.env.SAKTHAI_HOME = "/non/existent/path/sakthai";
    try {
      const req = new NextRequest("http://localhost:3000/api/gateway/memory/edit", {
        method: "POST",
        body: JSON.stringify({ id: 999, persona: "sakthai", value: "test value" }),
      });
      const res = await editPOST(req);
      expect(res.status).toBe(404);
      const json = await res.json();
      expect(json.ok).toBe(false);
    } finally {
      process.env.SAKTHAI_HOME = prevHome;
    }
  });

  it("successfully updates fact in local SQLite shard on fallback", async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "sak-memory-test-"));
    const personaDir = path.join(tmpDir, "sakthai");
    fs.mkdirSync(personaDir, { recursive: true });
    const dbPath = path.join(personaDir, "memory.db");

    const db = new Database(dbPath);
    db.exec(`
      CREATE TABLE facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL DEFAULT 'note',
        key TEXT,
        value TEXT NOT NULL,
        source_session TEXT,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL,
        tags TEXT
      );
      INSERT INTO facts (id, kind, key, value, created_at, updated_at, tags)
      VALUES (42, 'note', 'old_key', 'old value', 1700000000, 1700000000, '["initial"]');
    `);
    db.close();

    const prevHome = process.env.SAKTHAI_HOME;
    process.env.SAKTHAI_HOME = tmpDir;

    try {
      const req = new NextRequest("http://localhost:3000/api/gateway/memory/edit", {
        method: "POST",
        body: JSON.stringify({
          id: 42,
          persona: "sakthai",
          kind: "fact",
          key: "new_key",
          value: "updated value with secret sk-1234567890abcdef1234567890",
          tags: ["curated", "verified"],
        }),
      });

      const res = await editPOST(req);
      expect(res.status).toBe(200);
      const json = await res.json();
      expect(json.ok).toBe(true);
      expect(json.status).toBe("success");
      expect(json.source).toBe("sqlite_direct");
      expect(json.fact.id).toBe(42);
      expect(json.fact.kind).toBe("fact");
      expect(json.fact.key).toBe("new_key");
      expect(json.fact.value).toContain("[REDACTED_API_KEY]");
      expect(json.fact.tags).toEqual(["curated", "verified"]);
      expect(json.fact.updated_at).toBeGreaterThan(1700000000);

      // Verify on-disk persistence
      const checkDb = new Database(dbPath);
      const row = checkDb.prepare("SELECT * FROM facts WHERE id = 42").get() as Record<string, unknown>;
      expect(row.key).toBe("new_key");
      expect(row.kind).toBe("fact");
      expect(row.value).toContain("[REDACTED_API_KEY]");
      checkDb.close();
    } finally {
      process.env.SAKTHAI_HOME = prevHome;
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });
});

describe("MemoryExplorer Curation & In-Place Editing UI", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/gateway/memory/shards")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              ok: true,
              shards: [
                {
                  persona: "sakthai",
                  name: "SakThai",
                  role: "Master Coordinator",
                  size_bytes: 4096,
                  facts_count: 2,
                  observations_count: 1,
                },
              ],
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ ok: true, facts: [] }),
      });
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  const MOCK_MEMORY: MemoryPayload = {
    total_facts: 2,
    total_observations: 1,
    facts_this_week: 1,
    observations_this_week: 1,
    fact_growth: { labels: [], values: [] },
    observation_growth: { labels: [], values: [] },
    kind_counts: { fact: 1, secret: 1 },
    facts: [
      {
        id: 1,
        persona: "sakthai",
        kind: "fact",
        key: "system_architecture",
        value: "Local-first distributed AI agent family",
        tags: ["arch", "fleet"],
        created_at: 1700000000,
        updated_at: 1700000000,
      },
      {
        id: 2,
        persona: "sakthai",
        kind: "secret",
        key: "api_auth_token",
        value: "Production API gateway authorization token",
        tags: ["private", "credential"],
        created_at: 1700000100,
        updated_at: 1700000100,
      },
    ],
    observations: [
      {
        id: 1,
        persona: "sakthai",
        summary: "Autonomous workflows completed successfully",
        weight: 1.0,
        confidence: 0.95,
        created_at: 1700000200,
      },
    ],
  };

  it("renders Private badges for sensitive facts and tag chips", async () => {
    await act(async () => {
      render(<MemoryExplorer memory={MOCK_MEMORY} />);
    });

    // Secret fact should display Private badge
    const privateBadges = screen.getAllByText("Private");
    expect(privateBadges.length).toBeGreaterThan(0);

    // Tag chips should be rendered
    expect(screen.getByText("#arch")).toBeInTheDocument();
    expect(screen.getByText("#private")).toBeInTheDocument();
  });

  it("opens Edit Fact modal when clicking Edit button and submits updates", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string, opts?: RequestInit) => {
      if (url.includes("/api/gateway/memory/edit") && opts?.method === "POST") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              ok: true,
              status: "success",
              fact: {
                id: 1,
                persona: "sakthai",
                kind: "fact",
                key: "system_architecture",
                value: "Updated distributed AI agent architecture",
                tags: ["arch", "updated"],
                updated_at: 1700001000,
              },
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ ok: true, shards: [], facts: [] }),
      });
    });
    global.fetch = fetchMock;

    await act(async () => {
      render(<MemoryExplorer memory={MOCK_MEMORY} />);
    });

    // Find and click the edit button for Fact #1
    const editButtons = screen.getAllByTitle("Edit memory fact");
    expect(editButtons.length).toBe(2);
    fireEvent.click(editButtons[0]);

    // Modal should be visible
    expect(screen.getByText(/Edit Memory Fact \(ID #1\)/i)).toBeInTheDocument();

    // Verify populated value
    const valueInput = screen.getByLabelText(/Fact Content \/ Value:/i);
    expect(valueInput).toHaveValue("Local-first distributed AI agent family");

    // Change value
    fireEvent.change(valueInput, {
      target: { value: "Updated distributed AI agent architecture" },
    });

    // Submit form
    const submitBtn = screen.getByRole("button", { name: /Save Changes/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/gateway/memory/edit",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("Updated distributed AI agent architecture"),
        })
      );
    });
  });
});
