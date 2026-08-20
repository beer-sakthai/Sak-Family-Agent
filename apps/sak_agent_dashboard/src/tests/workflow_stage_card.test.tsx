import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { WorkflowStageCard } from "../components/WorkflowStageCard";
import { WorkflowStage } from "../lib/types";

const mockStage: WorkflowStage = {
  id: "stage_1",
  name: "System Telemetry & Health Audit",
  personaSlug: "sakthai",
  personaName: "SakThai",
  action: "Run full health scan and check active model connections",
  provider: "claude",
  model: "claude-3-7-sonnet",
  status: "completed",
  params: { scanDepth: "full", auditGuardrails: true },
  output: { healthScore: 0.99, activeNodes: 6 },
};

describe("WorkflowStageCard Component Accessibility & Interactions", () => {
  it("renders as a button with proper ARIA attributes when onToggleExpand is provided", () => {
    const onToggle = vi.fn();
    render(
      <WorkflowStageCard
        stage={mockStage}
        index={0}
        isExpanded={false}
        onToggleExpand={onToggle}
      />
    );

    const button = screen.getByRole("button", {
      name: "Toggle details for stage 1: System Telemetry & Health Audit",
    });

    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(button.tagName.toLowerCase()).toBe("button");

    fireEvent.click(button);
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it("reflects expanded state and renders parameter details when isExpanded is true", () => {
    render(
      <WorkflowStageCard
        stage={mockStage}
        index={0}
        isExpanded={true}
        onToggleExpand={() => {}}
      />
    );

    const button = screen.getByRole("button", {
      name: "Toggle details for stage 1: System Telemetry & Health Audit",
    });
    expect(button).toHaveAttribute("aria-expanded", "true");

    expect(screen.getByText("Parameters")).toBeInTheDocument();
    expect(screen.getByText("State Output")).toBeInTheDocument();
  });

  it("renders as non-interactive div when onToggleExpand is undefined", () => {
    const { container } = render(
      <WorkflowStageCard stage={mockStage} index={0} isExpanded={false} />
    );

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(container.firstChild?.nodeName.toLowerCase()).toBe("div");
  });
});
