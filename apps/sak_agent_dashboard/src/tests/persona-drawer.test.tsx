/**
 * The per-persona detail drawer.
 *
 * The shares are the whole point of the surface, so they get the most
 * attention here: a share is a ratio against a family total, and every ratio
 * has a denominator that can be zero.
 */

import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import PersonaDrawer from "@/components/PersonaDrawer";
import type { PersonaSummary } from "@/lib/contracts.generated";
import { demoPersonas } from "@/lib/demo";

const family = demoPersonas().personas;
const busiest = [...family].sort((a, b) => b.runs - a.runs)[0];
const idle = family.find((persona) => persona.runs === 0 && !persona.has_shard)!;

function renderDrawer(persona: PersonaSummary, overrides: Partial<{
  filtered: boolean;
  onToggleFilter: () => void;
  onNavigate: (tab: never) => void;
  onClose: () => void;
}> = {}) {
  return render(
    <PersonaDrawer
      persona={persona}
      family={family}
      filtered={overrides.filtered ?? false}
      onToggleFilter={overrides.onToggleFilter ?? vi.fn()}
      onNavigate={(overrides.onNavigate ?? vi.fn()) as never}
      onClose={overrides.onClose ?? vi.fn()}
    />,
  );
}

describe("PersonaDrawer", () => {
  it("titles itself with the persona's display name", () => {
    renderDrawer(busiest);
    expect(screen.getByText(busiest.display_name)).toBeInTheDocument();
  });

  it("states each figure as a share of the family, not as a bare count", () => {
    renderDrawer(busiest);
    // Runs is the one share every demo persona has a denominator for.
    const familyRuns = family.reduce((sum, persona) => sum + persona.runs, 0);
    const expected = Math.round((busiest.runs / familyRuns) * 100);
    expect(screen.getAllByText(`${expected}% of family`).length).toBeGreaterThan(0);
  });

  it("says so rather than printing NaN when the family total is zero", () => {
    // A whole family with no errors leaves the error share with no denominator.
    const clean = family.map((persona) => ({ ...persona, errors: 0 }));
    render(
      <PersonaDrawer
        persona={clean[0]}
        family={clean}
        filtered={false}
        onToggleFilter={vi.fn()}
        onNavigate={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    expect(screen.getAllByText("no family total").length).toBeGreaterThan(0);
    expect(screen.queryByText(/NaN/)).not.toBeInTheDocument();
  });

  it("computes a success rate rather than asserting one", () => {
    renderDrawer(busiest);
    const rate = ((busiest.runs - busiest.errors) / busiest.runs) * 100;
    expect(screen.getByText(`${rate.toFixed(1)}%`)).toBeInTheDocument();
  });

  it("says a persona with no runs has none instead of inventing a score", () => {
    renderDrawer(idle);
    expect(screen.getByText("no runs yet")).toBeInTheDocument();
  });

  it("names the shard path a persona has", () => {
    renderDrawer(busiest);
    expect(screen.getByText(`~/.sakthai/${busiest.name}/memory.db`)).toBeInTheDocument();
  });

  it("explains a missing shard as not-yet-written rather than as an error", () => {
    renderDrawer(idle);
    expect(screen.getByText(/No shard yet/)).toBeInTheDocument();
  });

  it("reports the filter toggle upward instead of filtering itself", () => {
    const onToggleFilter = vi.fn();
    renderDrawer(busiest, { onToggleFilter });
    fireEvent.click(screen.getByRole("button", { name: new RegExp(`^Filter to this persona`) }));
    expect(onToggleFilter).toHaveBeenCalledTimes(1);
  });

  it("marks the toggle pressed and provides WCAG 2.5.3 compliant aria-label when persona is already in filter", () => {
    const { rerender } = renderDrawer(busiest, { filtered: true });
    const inFilterBtn = screen.getByRole("button", { name: new RegExp(`^In the filter`) });
    expect(inFilterBtn).toHaveAttribute("aria-pressed", "true");
    expect(inFilterBtn).toHaveAttribute(
      "aria-label",
      `In the filter - clear filter for ${busiest.display_name}`,
    );

    rerender(
      <PersonaDrawer
        persona={busiest}
        family={family}
        filtered={false}
        onToggleFilter={vi.fn()}
        onNavigate={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    const filterBtn = screen.getByRole("button", { name: new RegExp(`^Filter to this persona`) });
    expect(filterBtn).toHaveAttribute("aria-pressed", "false");
    expect(filterBtn).toHaveAttribute(
      "aria-label",
      `Filter to this persona - filter dashboard to ${busiest.display_name}`,
    );
  });

  it("provides informative title hover tooltips on summary metric tiles", () => {
    renderDrawer(busiest);
    const providerTile = screen.getByTitle(`Model provider: ${busiest.provider || "unset"}`);
    expect(providerTile).toBeInTheDocument();

    const modelTile = screen.getByTitle(`Configured model: ${busiest.model || "unset"}`);
    expect(modelTile).toBeInTheDocument();

    const latencyTile = screen.getByTitle(new RegExp(`^Average latency:`));
    expect(latencyTile).toBeInTheDocument();

    const rate = ((busiest.runs - busiest.errors) / busiest.runs) * 100;
    const successTile = screen.getByTitle(`Success rate: ${rate.toFixed(1)}%`);
    expect(successTile).toBeInTheDocument();
  });

  it("provides informative title tooltips on share metric rows", () => {
    renderDrawer(busiest);
    const familyRuns = family.reduce((sum, persona) => sum + persona.runs, 0);
    const expectedRuns = Math.round((busiest.runs / familyRuns) * 100);
    expect(screen.getByText("Runs").closest("div[title]")).toHaveAttribute(
      "title",
      `Runs: ${busiest.runs.toLocaleString()} (${expectedRuns}% of family total)`,
    );
  });

  it("renders progressbars with proper ARIA accessibility attributes", () => {
    renderDrawer(busiest);
    const familyRuns = family.reduce((sum, persona) => sum + persona.runs, 0);
    const expectedRuns = Math.round((busiest.runs / familyRuns) * 100);
    const runsBar = screen.getByRole("progressbar", { name: "Runs share of family" });
    expect(runsBar).toBeInTheDocument();
    expect(runsBar).toHaveAttribute("aria-valuenow", expectedRuns.toString());
    expect(runsBar).toHaveAttribute("aria-valuemin", "0");
    expect(runsBar).toHaveAttribute("aria-valuemax", "100");
    expect(runsBar).toHaveAttribute("aria-valuetext", `${expectedRuns}% of family`);
  });

  it("provides informative title tooltips and WCAG 2.5.3 compliant aria-labels on quick action navigation buttons", () => {
    renderDrawer(busiest);
    const sessionsBtn = screen.getByRole("button", { name: /Sessions/ });
    expect(sessionsBtn).toHaveAttribute(
      "title",
      `View sessions for ${busiest.display_name}`,
    );
    expect(sessionsBtn).toHaveAttribute(
      "aria-label",
      `Sessions - view sessions for ${busiest.display_name}`,
    );

    const memoryBtn = screen.getByRole("button", { name: /Memory/ });
    expect(memoryBtn).toHaveAttribute(
      "title",
      `View memory for ${busiest.display_name}`,
    );
    expect(memoryBtn).toHaveAttribute(
      "aria-label",
      `Memory - view memory for ${busiest.display_name}`,
    );

    const analyticsBtn = screen.getByRole("button", { name: /Analytics/ });
    expect(analyticsBtn).toHaveAttribute(
      "title",
      `View analytics for ${busiest.display_name}`,
    );
    expect(analyticsBtn).toHaveAttribute(
      "aria-label",
      `Analytics - view analytics for ${busiest.display_name}`,
    );
  });

  it("navigates to a panel rather than fetching anything itself", () => {
    const onNavigate = vi.fn();
    renderDrawer(busiest, { onNavigate });
    fireEvent.click(screen.getByRole("button", { name: /Sessions/ }));
    expect(onNavigate).toHaveBeenCalledWith("sessions");
  });

  it("closes through the parent", () => {
    const onClose = vi.fn();
    renderDrawer(busiest, { onClose });
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });
});
