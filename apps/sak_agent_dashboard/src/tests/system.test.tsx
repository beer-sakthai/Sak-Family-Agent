/**
 * The System view — the one section that shows real data on a hosted deploy.
 *
 * The totals are pure and tested directly against a small fixture; the render
 * tests check that the view says what it shows (real data, which commit) and
 * that its two controls — the workflow filter and the CLI groups — work. A
 * last block checks the committed snapshot against the contract, so a snapshot
 * generated from a stale persona list fails here rather than on the page.
 */

import React from "react";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import SystemView from "@/components/SystemView";
import { PERSONA_NAMES } from "@/lib/contracts.generated";
import { isTabId, NAV_ITEMS } from "@/lib/nav";
import {
  SYSTEM_SNAPSHOT,
  countLeafCommands,
  linesOf,
  systemTotals,
  type SystemSnapshot,
} from "@/lib/system";

const FIXTURE: SystemSnapshot = {
  meta: { source_commit: "abc1234", source_date: "2026-09-26T08:00:00+00:00", generator: "gen" },
  personas: [
    {
      name: "sakthai",
      lead: true,
      role: "Main Lead",
      domain: "HF",
      provider: "huggingface",
      model: "m-1",
      skill_count: 10,
      mcp_servers: ["hf"],
    },
    {
      name: "saktan",
      lead: false,
      role: "Ops",
      domain: "Rhythm",
      provider: null,
      model: null,
      skill_count: 4,
      mcp_servers: [],
    },
  ],
  package: [
    { name: "agent", kind: "package", files: 3, lines: 900 },
    { name: "config", kind: "module", files: 1, lines: 100 },
  ],
  tools: [
    { name: "learn", summary: "Store a fact.", mcp_only: false },
    { name: "run_agent_loop", summary: "Run a nested loop.", mcp_only: true },
  ],
  cli: {
    name: "sakthai",
    help: "",
    commands: [
      { name: "run", help: "Run a task." },
      {
        name: "memory",
        help: "Inspect memory.",
        commands: [
          { name: "show", help: "Show facts." },
          { name: "stats", help: "Counts." },
        ],
      },
    ],
  },
  workflows: [
    { file: "ci.yml", name: "CI", triggers: ["pull_request", "push"], gates_prs: true, jobs: ["test"] },
    { file: "stale.yml", name: "Stale", triggers: ["schedule"], gates_prs: false, jobs: ["stale"] },
  ],
  tests: {
    coverage_floor: 96,
    test_functions: 1234,
    trees: [{ name: "sakthai (tests/)", path: "tests", files: 100, runner: "ci.yml" }],
  },
  skills: { shared: ["Sak-dogfood"], library_categories: [{ name: "coding", skills: 5 }] },
};

describe("systemTotals", () => {
  it("sums skills across personas, shared and library", () => {
    const totals = systemTotals(FIXTURE);
    expect(totals.personaSkills).toBe(14);
    expect(totals.sharedSkills).toBe(1);
    expect(totals.librarySkills).toBe(5);
  });

  it("counts leaf commands, not groups", () => {
    // run + memory show + memory stats; `memory` itself is not runnable.
    expect(countLeafCommands(FIXTURE.cli)).toBe(3);
    expect(systemTotals(FIXTURE).cliCommands).toBe(3);
  });

  it("separates MCP-only tools and PR-gating workflows", () => {
    const totals = systemTotals(FIXTURE);
    expect(totals.tools).toBe(2);
    expect(totals.mcpOnlyTools).toBe(1);
    expect(totals.workflows).toBe(2);
    expect(totals.prWorkflows).toBe(1);
  });

  it("reads a module's lines, and 0 for one it does not have", () => {
    expect(linesOf(FIXTURE, "agent")).toBe(900);
    expect(linesOf(FIXTURE, "nope")).toBe(0);
  });
});

describe("SystemView", () => {
  it("says the data is real and which commit it describes", () => {
    render(<SystemView snapshot={FIXTURE} />);
    expect(screen.getByText("Real data.")).toBeInTheDocument();
    expect(screen.getByText(/commit abc1234/)).toBeInTheDocument();
  });

  it("marks the lead persona and the MCP-only tool", () => {
    render(<SystemView snapshot={FIXTURE} />);
    expect(screen.getByText("Lead")).toBeInTheDocument();
    expect(screen.getByText("MCP only")).toBeInTheDocument();
    expect(screen.getByText("No MCP servers")).toBeInTheDocument();
    // A persona with no configured model says so rather than printing "null".
    expect(screen.getByText("provider default")).toBeInTheDocument();
  });

  it("shows only PR-gating workflows until asked for all", () => {
    render(<SystemView snapshot={FIXTURE} />);
    const panel = screen.getByRole("region", { name: "Workflows" });
    expect(within(panel).getByText("ci.yml")).toBeInTheDocument();
    expect(within(panel).queryByText("stale.yml")).not.toBeInTheDocument();

    fireEvent.click(within(panel).getByRole("button", { name: "All 2" }));
    expect(within(panel).getByText("stale.yml")).toBeInTheDocument();
    expect(within(panel).getByRole("button", { name: "All 2" })).toHaveAttribute("aria-pressed", "true");
  });

  it("lists CLI groups with their subcommands", () => {
    render(<SystemView snapshot={FIXTURE} />);
    const tree = screen.getByRole("list", { name: "sakthai memory subcommands" });
    expect(within(tree).getByText("show")).toBeInTheDocument();
    expect(within(tree).getByText("stats")).toBeInTheDocument();
  });
});

describe("navigation", () => {
  it("offers System as a section, first in the list", () => {
    expect(isTabId("system")).toBe(true);
    expect(NAV_ITEMS[0].id).toBe("system");
  });
});

describe("the committed snapshot", () => {
  it("covers exactly the personas the contract defines, with one lead", () => {
    expect(SYSTEM_SNAPSHOT.personas.map((p) => p.name).sort()).toEqual([...PERSONA_NAMES].sort());
    expect(SYSTEM_SNAPSHOT.personas.filter((p) => p.lead)).toHaveLength(1);
  });

  it("renders without throwing", () => {
    render(<SystemView />);
    expect(screen.getByTestId("system-view")).toBeInTheDocument();
  });
});
