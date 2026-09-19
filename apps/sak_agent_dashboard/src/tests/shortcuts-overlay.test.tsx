import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

import ShortcutsOverlay from "@/components/ShortcutsOverlay";

function renderShortcutsOverlay(overrides: { onClose?: () => void } = {}) {
  const onClose = overrides.onClose ?? vi.fn();
  const result = render(<ShortcutsOverlay onClose={onClose} />);
  return { onClose, ...result };
}

describe("ShortcutsOverlay", () => {
  it("is an accessible dialog labelled by shortcuts title", () => {
    renderShortcutsOverlay();
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-labelledby", "shortcuts-title");
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
  });

  it("renders specific accessible label and shortcut hint on close button", () => {
    renderShortcutsOverlay();
    const closeBtn = screen.getByRole("button", { name: "Close keyboard shortcuts" });
    expect(closeBtn).toBeInTheDocument();
    expect(closeBtn).toHaveAttribute("type", "button");
    expect(closeBtn).toHaveAttribute("title", "Close keyboard shortcuts (Esc)");
    expect(closeBtn).toHaveTextContent("Esc");
    const backdropBtn = screen.getByRole("button", { name: "Dismiss keyboard shortcuts overlay backdrop" });
    expect(backdropBtn).toHaveAttribute("type", "button");
    expect(backdropBtn).toHaveAttribute("title", "Dismiss keyboard shortcuts overlay");
  });

  it("renders accessible key labels and title tooltips on shortcut tags", () => {
    renderShortcutsOverlay();
    const kbdTags = screen.getAllByText("⌘");
    expect(kbdTags[0]).toHaveAttribute("title", "Key: Command");
    expect(kbdTags[0]).toHaveAttribute("aria-label", "Key Command");
  });

  it("closes on close button click", () => {
    const { onClose } = renderShortcutsOverlay();
    const headerCloseButton = screen.getByRole("button", {
      name: "Close keyboard shortcuts",
    });
    fireEvent.click(headerCloseButton);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("closes on Escape key press", () => {
    const { onClose } = renderShortcutsOverlay();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("focuses the close button on open", () => {
    renderShortcutsOverlay();
    const headerCloseButton = screen.getByRole("button", {
      name: "Close keyboard shortcuts",
    });
    expect(document.activeElement).toBe(headerCloseButton);
  });

  it("renders key badges with accessible spoken labels for special key symbols", () => {
    renderShortcutsOverlay();
    expect(screen.getByLabelText("Key Command")).toBeInTheDocument();
    expect(screen.getByLabelText("Key Question mark")).toBeInTheDocument();
    expect(screen.getByLabelText("Key Left bracket")).toBeInTheDocument();
    expect(screen.getByLabelText("Key Escape")).toBeInTheDocument();
  });
});
