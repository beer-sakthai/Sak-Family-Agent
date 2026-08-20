import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { getHubEcosystemData } from "../lib/hub";
import { getSkillsCatalogData } from "../lib/skillsCatalog";
import { getBenchmarkArenaData } from "../lib/benchmarks";
import { getKnowledgeGraphData, getTelegramBridgeData } from "../lib/memoryRag";
import { getSelfEvolutionData } from "../lib/selfEvolution";

import { GET as getHubRoute } from "../app/api/hub/route";
import { GET as getSkillsRoute, POST as postSkillsRoute } from "../app/api/skills/route";
import { GET as getBenchmarksRoute } from "../app/api/benchmarks/route";
import { GET as getMemoryRagRoute, POST as postMemoryRagRoute } from "../app/api/memory/rag/route";
import { GET as getLearningRoute } from "../app/api/learning/route";
import { NextRequest } from "next/server";

import { HubEcosystemPanel } from "../components/HubEcosystemPanel";
import { SkillsToolsPanel } from "../components/SkillsToolsPanel";
import { BenchmarkArena } from "../components/BenchmarkArena";
import { MemoryRagTelegramPanel } from "../components/MemoryRagTelegramPanel";
import { SelfEvolutionPanel } from "../components/SelfEvolutionPanel";

describe("6-Part Cycle Data Libraries", () => {
  it("Part 1 (Dream): verifies Hub ecosystem catalog data", () => {
    const hub = getHubEcosystemData();
    expect(hub.totalModels).toBe(19);
    expect(hub.totalDatasets).toBe(16);
    expect(hub.totalSpaces).toBe(7);
    expect(hub.assets.length).toBeGreaterThan(0);
    const coreModel = hub.assets.find((a) => a.id === "sakthai-core");
    expect(coreModel?.meta.hasGGUF).toBe(true);
  });

  it("Part 2 (Hope): verifies Skills catalog and AST guardrail rules", () => {
    const skills = getSkillsCatalogData();
    expect(skills.totalSkills).toBeGreaterThanOrEqual(6);
    expect(skills.guardrails.length).toBeGreaterThanOrEqual(4);
    const repoOps = skills.skills.find((s) => s.slug === "repo-ops-pipeline");
    expect(repoOps?.authorPersona).toBe("SakJules");
  });

  it("Part 4 (Joy): verifies Benchmark arena leaderboard and metrics", () => {
    const bench = getBenchmarkArenaData();
    expect(bench.leaderboard).toHaveLength(6);
    expect(bench.evalCategories).toHaveLength(5);
    for (const score of bench.leaderboard) {
      expect(score.overallScore).toBeGreaterThan(80);
      expect(score.categoryScores.ToolAccuracy).toBeGreaterThan(85);
    }
  });

  it("Part 5 (Trust): verifies Memory Knowledge Graph and Telegram Bridge", () => {
    const graph = getKnowledgeGraphData();
    const telegram = getTelegramBridgeData();
    expect(graph.nodes.length).toBeGreaterThan(5);
    expect(graph.edges.length).toBeGreaterThan(3);
    expect(telegram.status).toBe("online");
    expect(telegram.registeredCommands).toContain("/workflows");
  });

  it("Part 6 (Growth): verifies Self-Evolution prompt diffs and journal", () => {
    const evo = getSelfEvolutionData();
    expect(evo.round).toBeGreaterThan(0);
    expect(evo.evolutions.length).toBeGreaterThan(0);
    expect(evo.journalEntries.length).toBeGreaterThan(0);
    expect(evo.mutationCoveragePct).toBeGreaterThan(90);
  });
});

describe("Cycle Backend API Route Handlers", () => {
  it("GET /api/hub returns catalog data with success true", async () => {
    const res = await getHubRoute();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.success).toBe(true);
    expect(body.data.totalModels).toBe(19);
  });

  it("GET & POST /api/skills handles catalog and simulated dispatch", async () => {
    const getRes = await getSkillsRoute();
    expect(getRes.status).toBe(200);
    const getBody = await getRes.json();
    expect(getBody.success).toBe(true);

    const postReq = new NextRequest("http://localhost:3000/api/skills", {
      method: "POST",
      body: JSON.stringify({
        skillSlug: "repo-ops-pipeline",
        targetPersona: "SakJules",
      }),
    });
    const postRes = await postSkillsRoute(postReq);
    expect(postRes.status).toBe(200);
    const postBody = await postRes.json();
    expect(postBody.success).toBe(true);
    expect(postBody.dispatched.status).toBe("executed");
  });

  it("GET /api/benchmarks returns leaderboard and categories", async () => {
    const res = await getBenchmarksRoute();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.success).toBe(true);
    expect(body.data.leaderboard).toHaveLength(6);
  });

  it("GET & POST /api/memory/rag handles knowledge query", async () => {
    const getRes = await getMemoryRagRoute();
    expect(getRes.status).toBe(200);
    const getBody = await getRes.json();
    expect(getBody.success).toBe(true);

    const postReq = new NextRequest("http://localhost:3000/api/memory/rag", {
      method: "POST",
      body: JSON.stringify({ query: "SakThai" }),
    });
    const postRes = await postMemoryRagRoute(postReq);
    expect(postRes.status).toBe(200);
    const postBody = await postRes.json();
    expect(postBody.success).toBe(true);
    expect(postBody.totalHits).toBeGreaterThanOrEqual(1);
  });

  it("GET /api/learning returns prompt evolutions and journal", async () => {
    const res = await getLearningRoute();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.success).toBe(true);
    expect(body.data.evolutions.length).toBeGreaterThan(0);
  });
});

describe("Cycle UI Components Render", () => {
  it("renders HubEcosystemPanel with assets and metrics", () => {
    render(<HubEcosystemPanel />);
    expect(screen.getByTestId("hub-ecosystem-panel")).toBeDefined();
    expect(screen.getAllByText(/Hugging Face Hub/i).length).toBeGreaterThan(0);
  });

  it("renders SkillsToolsPanel with AST firewall", () => {
    render(<SkillsToolsPanel />);
    expect(screen.getByTestId("skills-tools-panel")).toBeDefined();
    expect(screen.getAllByText(/Skills & AST Tool-Guardrails/i).length).toBeGreaterThan(0);
  });

  it("renders BenchmarkArena with rankings", () => {
    render(<BenchmarkArena />);
    expect(screen.getByTestId("benchmark-arena-panel")).toBeDefined();
    expect(screen.getAllByText(/Benchmark Arena/i).length).toBeGreaterThan(0);
  });

  it("renders MemoryRagTelegramPanel with SQLite graph", () => {
    render(<MemoryRagTelegramPanel />);
    expect(screen.getByTestId("memory-rag-telegram-panel")).toBeDefined();
    expect(screen.getAllByText(/Memory Vector RAG/i).length).toBeGreaterThan(0);
  });

  it("renders SelfEvolutionPanel with prompt diffs", () => {
    render(<SelfEvolutionPanel />);
    expect(screen.getByTestId("self-evolution-panel")).toBeDefined();
    expect(screen.getAllByText(/Self-Evolution & Continuous Learning Loop/i).length).toBeGreaterThan(0);
  });
});
