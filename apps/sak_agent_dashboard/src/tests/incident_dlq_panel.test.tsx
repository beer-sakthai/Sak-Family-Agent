import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { IncidentDLQPanel } from "../components/dashboard/panels/IncidentDLQPanel";

// Mock the nested SelfHealingConsole to verify it gets rendered
vi.mock("../components/SelfHealingConsole", () => ({
  SelfHealingConsole: () => <div data-testid="mock-self-healing-console">Mocked Self Healing Console</div>,
}));

describe("IncidentDLQPanel Component", () => {
  it("renders correctly with semantic section element", () => {
    // We add a wrapper with an id that matches aria-labelledby
    // so that the section can be found by role and name
    render(
      <div>
        <h2 id="dlq-incident-heading">DLQ Incidents</h2>
        <IncidentDLQPanel />
      </div>
    );
    const section = screen.getByRole("region", { name: "DLQ Incidents" });
    expect(section).toBeInTheDocument();
  });

  it("renders the SelfHealingConsole within the section", () => {
    render(
      <div>
        <h2 id="dlq-incident-heading">DLQ Incidents</h2>
        <IncidentDLQPanel />
      </div>
    );
    const consoleContent = screen.getByTestId("mock-self-healing-console");
    expect(consoleContent).toBeInTheDocument();
  });
});
