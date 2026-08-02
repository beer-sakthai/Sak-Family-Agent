import { render, screen } from "@testing-library/react";
import Home from "@/app/page";
import { describe, it, expect } from "vitest";

describe("Home Page & Root Layout Shell (Tier 1 & Tier 2)", () => {
  it("renders Sak-Agent-Family title and description banner", () => {
    render(<Home />);
    expect(screen.getByText("Sak-Agent-Family Runtime Intelligence")).toBeInTheDocument();
    expect(
      screen.getByText(/Real-time telemetry, session transcripts, memory SQLite store inspector/i)
    ).toBeInTheDocument();
  });

  it("renders all 5 personas with roles and status indicators", () => {
    render(<Home />);

    const personaNames = ["SakThai", "SakKing", "SakSee", "SakSit", "SakJules"];
    personaNames.forEach((name) => {
      expect(screen.getByText(name)).toBeInTheDocument();
    });

    expect(screen.getByText("Primary Orchestrator & Fine-Tuned Agent")).toBeInTheDocument();
    expect(screen.getByText("High-Capacity Reasoning Specialist")).toBeInTheDocument();
    expect(screen.getByText("Multimodal & Vision Specialist")).toBeInTheDocument();
    expect(screen.getByText("Code Review & Security Auditor")).toBeInTheDocument();
    expect(screen.getByText("Background Task & Async Execution Specialist")).toBeInTheDocument();
  });

  it("renders overview stat counters with expected values", () => {
    render(<Home />);

    expect(screen.getByText("761")).toBeInTheDocument();
    expect(screen.getByText("Recorded in runtime")).toBeInTheDocument();
    expect(screen.getByText("~/.sakthai")).toBeInTheDocument();
    expect(screen.getByText("100% Pass")).toBeInTheDocument();
  });
});
