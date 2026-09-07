import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import OperationsPulse from "@/components/OperationsPulse";
import { demoAudit, demoMetrics, demoPersonas, demoWorkflows } from "@/lib/demo";

describe("OperationsPulse", () => {
  it("summarises the four operational signals from the returned payloads", () => {
    render(
      <OperationsPulse
        personas={demoPersonas()}
        metrics={demoMetrics()}
        audit={demoAudit()}
        workflows={demoWorkflows()}
      />,
    );

    expect(screen.getByRole("heading", { name: "System pulse" })).toBeInTheDocument();
    expect(screen.getByText("5 / 6")).toBeInTheDocument();
    expect(screen.getByText("97.9%")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("2 / 4")).toBeInTheDocument();
    expect(screen.getByText(/2 high or critical events require review/)).toBeInTheDocument();
    expect(screen.getByText(/1 failed workflow run requires review/)).toBeInTheDocument();
  });

  it("opens the source panel behind each actionable signal", () => {
    const onNavigate = vi.fn();
    render(
      <OperationsPulse
        personas={demoPersonas()}
        metrics={demoMetrics()}
        audit={demoAudit()}
        workflows={demoWorkflows()}
        onNavigate={onNavigate}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Run quality: 97\.9%/ }));
    fireEvent.click(screen.getByRole("button", { name: /Security queue: 2/ }));
    fireEvent.click(screen.getByRole("button", { name: /Workflow health: 2 \/ 4/ }));

    expect(onNavigate).toHaveBeenNthCalledWith(1, "analytics");
    expect(onNavigate).toHaveBeenNthCalledWith(2, "audit");
    expect(onNavigate).toHaveBeenNthCalledWith(3, "workflows");
  });

  it("makes absent data visibly neutral instead of showing invented health", () => {
    render(<OperationsPulse personas={null} metrics={null} audit={null} workflows={null} />);

    expect(screen.getAllByText("—")).toHaveLength(4);
    expect(screen.getAllByText("Awaiting data")).toHaveLength(4);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
