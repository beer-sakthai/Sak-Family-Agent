import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GET as shardsGET } from "@/app/api/gateway/memory/shards/route";
import { POST as mutatePOST, DELETE as mutateDELETE } from "@/app/api/gateway/memory/mutate/route";
import { POST as previewPOST } from "@/app/api/gateway/memory/preview/route";
import { MemoryExplorer } from "@/components/MemoryExplorer";
import { NextRequest } from "next/server";
import type { MemoryPayload } from "@/lib/contracts.generated";

const MOCK_MEMORY: MemoryPayload = {
  total_facts: 5,
  total_observations: 2,
  facts_this_week: 1,
  observations_this_week: 1,
  fact_growth: { labels: [], values: [] },
  observation_growth: { labels: [], values: [] },
  kind_counts: { fact: 4, pref: 1 },
  facts: [
    {
      id: 1,
      persona: "sakthai",
      kind: "fact",
      key: "ci_config",
      value: "CI/CD automated pipeline running on Ubuntu 24.04",
      tags: ["ci"],
      created_at: 1700000000,
      updated_at: 1700000000,
    },
    {
      id: 2,
      persona: "sakjules",
      kind: "pref",
      key: "theme_preference",
      value: "User prefers dark mode layout",
      tags: ["ui"],
      created_at: 1700000100,
      updated_at: 1700000100,
    },
  ],
  observations: [
    {
      id: 1,
      persona: "sakthai",
      summary: "System completed multi-agent task successfully",
      weight: 1.0,
      confidence: 0.9,
      created_at: 1700000200,
    },
  ],
};


describe("Memory Shard Studio & Endpoints", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  describe("Memory Gateway API Routes", () => {
    it("shards route returns shard metadata", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          shards: [{ persona: "sakthai", name: "SakThai", facts_count: 5 }],
          total_facts: 5,
        }),
      });

      const res = await shardsGET();
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.ok).toBe(true);
      expect(data.shards.length).toBe(1);
    });

    it("mutate route POST proxies add fact", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ ok: true, status: "created", fact: { id: 1 } }),
      });

      const req = new NextRequest("http://localhost:3000/api/gateway/memory/mutate", {
        method: "POST",
        body: JSON.stringify({ persona: "sakjules", value: "New memory fact" }),
      });
      const res = await mutatePOST(req);
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.ok).toBe(true);
    });

    it("mutate route DELETE proxies delete fact", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ ok: true, status: "deleted" }),
      });

      const req = new NextRequest("http://localhost:3000/api/gateway/memory/mutate?id=1&persona=sakjules&confirmed=true", {
        method: "DELETE",
      });
      const res = await mutateDELETE(req);
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.ok).toBe(true);
    });

    it("preview route POST proxies memory context simulator", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          prompt_context: "### Persistent Memory Context for SakJules",
          facts: [],
          observations: [],
        }),
      });

      const req = new NextRequest("http://localhost:3000/api/gateway/memory/preview", {
        method: "POST",
        body: JSON.stringify({ persona: "sakjules", query: "CI tests" }),
      });
      const res = await previewPOST(req);
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.ok).toBe(true);
      expect(data.prompt_context).toContain("SakJules");
    });
  });

  describe("MemoryExplorer Studio Component", () => {
    it("renders shard selector buttons including All Shards and personas", () => {
      render(<MemoryExplorer memory={MOCK_MEMORY} />);

      expect(screen.getByText("Memory Shard Studio & Explorer")).toBeInTheDocument();
      expect(screen.getByText("All Shards (Merged)")).toBeInTheDocument();
      expect(screen.getByText("SakThai")).toBeInTheDocument();
      expect(screen.getByText("SakJules")).toBeInTheDocument();
      expect(screen.getByText("SakKing")).toBeInTheDocument();
      expect(screen.getByText("SakSee")).toBeInTheDocument();
      expect(screen.getByText("SakSit")).toBeInTheDocument();
      expect(screen.getByText("SakTan")).toBeInTheDocument();
    });

    it("renders kind filter chips", () => {
      render(<MemoryExplorer memory={MOCK_MEMORY} />);

      expect(screen.getByRole("button", { name: /^all$/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^fact$/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^pref$/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^goal$/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^pattern$/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^note$/i })).toBeInTheDocument();
    });

    it("opens Add Fact modal on button click", () => {
      render(<MemoryExplorer memory={MOCK_MEMORY} />);

      const addBtn = screen.getByText("Add Fact");
      fireEvent.click(addBtn);

      expect(screen.getByText("Add Persistent Memory Fact")).toBeInTheDocument();
      expect(screen.getByText("Target Persona Shard:")).toBeInTheDocument();
    });

    it("switches to Prompt Simulator sub-tab", () => {
      render(<MemoryExplorer memory={MOCK_MEMORY} />);

      const simTab = screen.getByText("Prompt Simulator");
      fireEvent.click(simTab);

      expect(screen.getByText("Prompt Injection Simulator")).toBeInTheDocument();
      expect(screen.getByText("Preview")).toBeInTheDocument();
    });
  });
});
