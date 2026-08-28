import { fireEvent, render, screen, within } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

import Drawer from "@/components/Drawer";

function renderDrawer(overrides: { onClose?: () => void } = {}) {
  const onClose = overrides.onClose ?? vi.fn();
  const result = render(
    <Drawer title="Session transcript" subtitle="1700000000_abc" onClose={onClose}>
      <button>inner one</button>
      <button>inner two</button>
    </Drawer>,
  );
  return { onClose, ...result };
}

describe("Drawer", () => {
  it("is an accessible dialog labelled by its title", () => {
    renderDrawer();
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-label", "Session transcript");
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
  });

  it("renders its subtitle", () => {
    renderDrawer();
    expect(screen.getByText("1700000000_abc")).toBeInTheDocument();
  });

  it("closes on the close button", () => {
    const { onClose } = renderDrawer();
    fireEvent.click(screen.getByLabelText("Close"));
    expect(onClose).toHaveBeenCalled();
  });

  it("closes on Escape", () => {
    const { onClose } = renderDrawer();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });

  it("ignores other keys", () => {
    const { onClose } = renderDrawer();
    fireEvent.keyDown(document, { key: "a" });
    expect(onClose).not.toHaveBeenCalled();
  });

  it("closes on the scrim, which is a real button", () => {
    const { onClose } = renderDrawer();
    // The modal this replaces used a <div onClick> — unreachable by keyboard.
    fireEvent.click(screen.getByLabelText("Close detail"));
    expect(onClose).toHaveBeenCalled();
  });

  it("moves focus into the drawer on open", () => {
    renderDrawer();
    expect(document.activeElement).toBe(screen.getByLabelText("Close"));
  });

  it("returns focus to the opener on unmount", () => {
    const opener = document.createElement("button");
    document.body.appendChild(opener);
    opener.focus();

    const { unmount } = renderDrawer();
    expect(document.activeElement).not.toBe(opener);

    unmount();
    expect(document.activeElement).toBe(opener);
    opener.remove();
  });

  it("locks the page behind it and restores scrolling on close", () => {
    const { unmount } = renderDrawer();
    expect(document.body.style.overflow).toBe("hidden");
    unmount();
    expect(document.body.style.overflow).toBe("");
  });

  // The trap covers the panel, not the scrim: the scrim is a sibling of the
  // dialog, so `getAllByRole("button")` on the whole screen would include a
  // control the trap deliberately excludes.
  function panelButtons(): HTMLElement[] {
    return within(screen.getByRole("dialog")).getAllByRole("button");
  }

  it("wraps Tab from the last control back to the first", () => {
    renderDrawer();
    const buttons = panelButtons();
    buttons[buttons.length - 1].focus();
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(buttons[0]);
  });

  it("wraps Shift+Tab from the first control to the last", () => {
    renderDrawer();
    const buttons = panelButtons();
    buttons[0].focus();
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(buttons[buttons.length - 1]);
  });

  it("leaves Tab alone in the middle of the panel", () => {
    renderDrawer();
    const buttons = panelButtons();
    buttons[1].focus();
    fireEvent.keyDown(document, { key: "Tab" });
    // Not intercepted: the browser's own tab order takes it from here.
    expect(document.activeElement).toBe(buttons[1]);
  });
});
