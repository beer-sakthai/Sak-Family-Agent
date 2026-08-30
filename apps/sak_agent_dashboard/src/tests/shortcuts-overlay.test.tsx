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

  it("renders specific accessible label on close button", () => {
    renderShortcutsOverlay();
    expect(
      screen.getByRole("button", { name: "Close keyboard shortcuts overlay" }),
    ).toBeInTheDocument();
  });

  it("closes on close button click", () => {
    const { onClose } = renderShortcutsOverlay();
    const headerCloseButton = screen.getByRole("button", {
      name: "Close keyboard shortcuts overlay",
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
      name: "Close keyboard shortcuts overlay",
    });
    expect(document.activeElement).toBe(headerCloseButton);
  });
});
