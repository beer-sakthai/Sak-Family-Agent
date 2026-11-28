import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import React from "react";

import { RunnerDrawer } from "@/components/RunnerDrawer";

describe("RunnerDrawer Component", () => {
  it("renders null when isOpen is false", () => {
    const { container } = render(
      <RunnerDrawer isOpen={false} onClose={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders drawer elements when isOpen is true", () => {
    render(<RunnerDrawer isOpen={true} onClose={vi.fn()} />);

    expect(screen.getByText("Universal Agent Runner")).toBeInTheDocument();
    expect(screen.getByText("Target Persona")).toBeInTheDocument();
    expect(screen.getByText("Prompt Presets")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Execute/i })).toBeInTheDocument();
  });

  it("switches selected persona when clicking persona badge", () => {
    render(<RunnerDrawer isOpen={true} onClose={vi.fn()} initialPersona="sakthai" />);

    // Click SakKing
    const sakkingBtn = screen.getByRole("button", { name: /SakKing/i });
    fireEvent.click(sakkingBtn);

    // Preset for SakKing should now appear
    expect(screen.getByText("Run fast test suite verification")).toBeInTheDocument();
  });

  it("populates instruction prompt when clicking a preset", () => {
    render(<RunnerDrawer isOpen={true} onClose={vi.fn()} initialPersona="sakjules" />);

    const presetBtn = screen.getByText("Check CI status and verify contracts");
    fireEvent.click(presetBtn);

    const textarea = screen.getByPlaceholderText(/Enter task prompt/i) as HTMLTextAreaElement;
    expect(textarea.value).toBe("Check CI status and verify contracts");
  });

  it("toggles dry-run checkbox state", () => {
    render(<RunnerDrawer isOpen={true} onClose={vi.fn()} />);

    const dryRunCheckbox = screen.getByLabelText(/Dry-run/i) as HTMLInputElement;
    expect(dryRunCheckbox.checked).toBe(true);

    fireEvent.click(dryRunCheckbox);
    expect(dryRunCheckbox.checked).toBe(false);
  });

  it("invokes onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(<RunnerDrawer isOpen={true} onClose={onClose} />);

    const closeBtn = screen.getByTitle(/Close Runner/i);
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
