import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { GET as autoCycleGet } from "../app/api/auto-cycle/route";
import { getAutoCycleData } from "../lib/autoCycle";
import AutoCyclePanel from "../components/AutoCyclePanel";

import { GET as specsGet } from "../app/api/design-specs/route";
import { getDesignSpecsData } from "../lib/designSpecs";
import DesignSpecsPanel from "../components/DesignSpecsPanel";

import { M365_ACCOUNT_BLOCKER, getM365CopilotData } from "../lib/m365Copilot";
import M365CopilotPanel from "../components/M365CopilotPanel";

describe("Auto-Cycle tab", () => {
  it("mirrors the six stages from cycle/stages.py in order", async () => {
    const data = getAutoCycleData();
    expect(data.stages.map((s) => s.stage)).toEqual([
      "dream",
      "hope",
      "care",
      "joy",
      "trust",
      "growth",
    ]);
    expect(data.stages.map((s) => s.number)).toEqual([1, 2, 3, 4, 5, 6]);
    // Every stage carries a goal, guidance, and at least one command.
    for (const s of data.stages) {
      expect(s.goal.length).toBeGreaterThan(0);
      expect(s.guidance.length).toBeGreaterThan(0);
      expect(s.commands.length).toBeGreaterThan(0);
    }

    const res = await autoCycleGet();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.autocycle.stages).toHaveLength(6);
  });

  it("lists all six personas with SakThai as lead", () => {
    const data = getAutoCycleData();
    expect(data.personas).toHaveLength(6);
    expect(data.personas.map((p) => p.persona)).toEqual(
      expect.arrayContaining([
        "SakKing",
        "SakThai",
        "SakSee",
        "SakSit",
        "SakTan",
        "SakJules",
      ])
    );
    const leads = data.personas.filter((p) => p.lead);
    expect(leads).toHaveLength(1);
    expect(leads[0].persona).toBe("SakThai");
  });

  it("caps rounds at 3 and describes both composing skills", () => {
    const data = getAutoCycleData();
    expect(data.roundCap).toBe(3);
    expect(data.skills).toHaveLength(2);
    expect(data.skills.map((s) => s.layer).sort()).toEqual([
      "claude-code",
      "shared",
    ]);
  });

  it("keeps the dry-run default as the safety rule, with a test command that is actually dry", () => {
    const { safetyRule } = getAutoCycleData();
    expect(safetyRule.testCommand).toContain("--dry-run");
    expect(safetyRule.testCommand).toContain("mktemp -d");
    // The test command must never reference a live persona home.
    expect(safetyRule.testCommand).not.toContain("/opt/data");
    expect(safetyRule.nonAuthorizationPhrases.length).toBeGreaterThanOrEqual(4);
    expect(safetyRule.baselineEvidence).toMatch(/5/);
  });

  it("panel surfaces the safety rule, stages, and live-home warning", () => {
    render(<AutoCyclePanel data={getAutoCycleData()} />);
    expect(
      screen.getByText(/Default to a dry, throwaway run/i)
    ).toBeInTheDocument();
    expect(screen.getAllByText(/dream/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/growth/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Why this rule exists/i)).toBeInTheDocument();
    expect(screen.getAllByText(/lead/i).length).toBeGreaterThan(0);
  });

  it("panel renders loading state when data is null", () => {
    render(<AutoCyclePanel data={null} />);
    expect(screen.getByText(/Loading auto-cycle definition/i)).toBeInTheDocument();
  });
});

describe("Design Specs tab", () => {
  it("reads the real specs directory and parses status from each file", async () => {
    const data = getDesignSpecsData();
    expect(data.present).toBe(true);
    expect(data.specs.length).toBeGreaterThanOrEqual(7);

    // Status must be derived, not hardcoded — at least one approved and one draft.
    const statuses = new Set(data.specs.map((s) => s.status));
    expect(statuses.has("approved")).toBe(true);
    expect(statuses.has("draft")).toBe(true);

    // Every spec has a title parsed from its H1 and a date from its filename.
    for (const s of data.specs) {
      expect(s.title.length).toBeGreaterThan(0);
      expect(s.date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(s.bytes).toBeGreaterThan(0);
    }

    const res = await specsGet();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.success).toBe(true);
  });

  it("pairs specs with their implementation plans where one exists", () => {
    const data = getDesignSpecsData();
    const autoCycleSpec = data.specs.find((s) =>
      s.file.includes("sak-family-auto-cycle-design")
    );
    expect(autoCycleSpec).toBeDefined();
    expect(autoCycleSpec!.planFile).toBe(
      "docs/superpowers/plans/2026-07-08-sak-family-auto-cycle.md"
    );
  });

  it("sorts newest first", () => {
    const dates = getDesignSpecsData().specs.map((s) => s.date);
    expect(dates).toEqual([...dates].sort().reverse());
  });

  it("panel renders spec cards and filters by status", () => {
    const data = getDesignSpecsData();
    render(<DesignSpecsPanel data={data} />);
    expect(screen.getByText(/Design Specs/i)).toBeInTheDocument();
    const draftBtn = screen.getByRole("button", { name: /^draft \(/i });
    fireEvent.click(draftBtn);
    // After filtering to draft, an approved-only spec title should be gone.
    const approvedTitles = data.specs
      .filter((s) => s.status === "approved")
      .map((s) => s.title);
    if (approvedTitles.length > 0) {
      expect(screen.queryByText(approvedTitles[0])).toBeNull();
    }
  });

  it("panel renders the not-found state when the directory is absent", () => {
    render(
      <DesignSpecsPanel
        data={{ present: false, specsDir: "", plansDir: "", specs: [] }}
      />
    );
    expect(screen.getByText(/No specs directory found/i)).toBeInTheDocument();
  });
});

describe("M365 tab — account-type blocker correction", () => {
  it("states that personal accounts are blocked under BOTH auth modes", () => {
    expect(M365_ACCOUNT_BLOCKER.body).toMatch(/personal Microsoft account/i);
    expect(M365_ACCOUNT_BLOCKER.body).toMatch(/delegated or application/i);
    expect(M365_ACCOUNT_BLOCKER.ruledOutAlternatives.length).toBeGreaterThanOrEqual(2);
    expect(M365_ACCOUNT_BLOCKER.viablePath).toMatch(/Cowork/);
    expect(M365_ACCOUNT_BLOCKER.specPath).toContain("cowork-plugin-design");
  });

  it("no longer claims delegated auth alone unlocks Copilot Retrieval", () => {
    const row = getM365CopilotData().contrastWithTeamsMcp.find(
      (r) => r.dimension === "Copilot Retrieval"
    )!;
    expect(row.m365Sdk).toMatch(/work\/school tenant/i);
    expect(row.m365Sdk).toMatch(/NOT usable on a personal/i);
  });

  it("panel surfaces the blocker above the install steps", () => {
    render(<M365CopilotPanel data={getM365CopilotData()} />);
    expect(
      screen.getByText(/Account type gates this before auth mode does/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Also ruled out/i)).toBeInTheDocument();
    expect(screen.getByText(/The path that does work/i)).toBeInTheDocument();
  });
});
