import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { IncidentDLQPanel } from "../components/dashboard/panels/IncidentDLQPanel";
import { SelfHealingConsole } from "../components/SelfHealingConsole";

// Mock hooks for rendering SelfHealingConsole
vi.mock("../lib/hooks/usePanelFetch", () => ({
  usePanelFetch: () => ({
    data: {
      success: true,
      data: {
        health: [
          { persona: "SakTan", circuitBreaker: "OPEN", failureCount: 3, pendingDlqCount: 1 },
          { persona: "SakNode", circuitBreaker: "CLOSED", failureCount: 0, pendingDlqCount: 0 },
        ],
        incidents: [
          { id: "inc-1", persona: "SakTan", action: "db_query", errorMessage: "Timeout", status: "pending", retryCount: 1, maxRetries: 3 },
        ],
      },
    },
    loading: false,
    refresh: vi.fn(),
  }),
}));

describe("IncidentDLQPanel & SelfHealingConsole Component", () => {
  it("renders correctly with semantic section element", () => {
    render(
      <div>
        <h2 id="dlq-incident-heading">DLQ Incidents</h2>
        <IncidentDLQPanel />
      </div>
    );
    const section = screen.getByRole("region", { name: "DLQ Incidents" });
    expect(section).toBeInTheDocument();
  });

  it("renders SelfHealingConsole with accessible buttons and keyboard focus rings", () => {
    render(<SelfHealingConsole />);

    const refreshBtn = screen.getByRole("button", { name: "Refresh recovery telemetry state" });
    expect(refreshBtn).toBeInTheDocument();
    expect(refreshBtn.className).toContain("focus-visible:ring-2");

    const resetBtn = screen.getByRole("button", { name: "Reset circuit breaker for SakTan" });
    expect(resetBtn).toBeInTheDocument();
    expect(resetBtn.className).toContain("focus-visible:ring-2");

    const replayBtn = screen.getByRole("button", { name: "Replay DLQ incident inc-1 for SakTan" });
    expect(replayBtn).toBeInTheDocument();
    expect(replayBtn.className).toContain("focus-visible:ring-2");
  });
});
