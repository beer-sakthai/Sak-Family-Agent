import { render, screen } from "@testing-library/react";
import Home from "@/app/page";
import { describe, it, expect } from "vitest";
import { PERSONAS } from "@/lib/personas";
import { DEMO_TOTAL_RUNS } from "@/lib/demoData";

describe("Home Page & Root Layout Shell (Tier 1 & Tier 2)", () => {
  it("renders Sak-Agent-Family title and description banner", () => {
    render(<Home />);
    expect(screen.getByText("Sak-Agent-Family Runtime Intelligence")).toBeInTheDocument();
    expect(
      screen.getByText(/Real-time telemetry, session transcripts, memory SQLite store inspector/i)
    ).toBeInTheDocument();
  });

  it("renders every persona in the roster, with its real role", () => {
    render(<Home />);

    // Asserted against lib/personas.ts rather than a literal list. The previous
    // version named five personas and five invented roles ("Primary
    // Orchestrator & Fine-Tuned Agent", "High-Capacity Reasoning Specialist",
    // ...), none of which matched the SOUL.md roster — which is how SakTan's
    // absence from the dashboard stayed invisible.
    expect(PERSONAS).toHaveLength(6);

    for (const persona of PERSONAS) {
      expect(
        screen.getAllByText(persona.name).length,
        `persona ${persona.name} not rendered`
      ).toBeGreaterThan(0);
      expect(
        screen.getAllByText(persona.role).length,
        `role for ${persona.name} not rendered`
      ).toBeGreaterThan(0);
    }
  });

  it("renders SakTan, which the dashboard previously omitted", () => {
    render(<Home />);
    expect(screen.getAllByText("SakTan").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Daily Ops · Deputy 2").length).toBeGreaterThan(0);
  });

  it("renders overview stat counters from the shared demo totals", () => {
    render(<Home />);

    // Derived from the per-persona demo run counts, not a literal, so the
    // counter cannot drift from the demo session list the way 761 had.
    expect(screen.getByText(String(DEMO_TOTAL_RUNS))).toBeInTheDocument();
    expect(screen.getByText("Recorded in runtime")).toBeInTheDocument();
    expect(screen.getByText("~/.sakthai")).toBeInTheDocument();
    expect(screen.getByText("100% Pass")).toBeInTheDocument();
  });
});
