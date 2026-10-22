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
    expect(kbdTags[0]).toHaveAttribute("aria-hidden", "true");
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
    expect(screen.getByText("(Command + K)")).toBeInTheDocument();
    expect(screen.getByText("(Slash)")).toBeInTheDocument();
    expect(screen.getByText("(Question mark)")).toBeInTheDocument();
    expect(screen.getByText("(Left bracket)")).toBeInTheDocument();
    expect(screen.getByText("(Escape)")).toBeInTheDocument();
  });

  it("filters shortcuts by search query and allows clearing the search", () => {
    renderShortcutsOverlay();
    const searchInput = screen.getByRole("searchbox", { name: "Filter keyboard shortcuts" });
    expect(searchInput).toBeInTheDocument();

    // Search for "command"
    fireEvent.change(searchInput, { target: { value: "command" } });
    expect(screen.getByText("Open the command palette")).toBeInTheDocument();
    expect(screen.queryByText("Show this list")).not.toBeInTheDocument();

    // Live status announcement for non-zero match count
    const liveStatus = screen.getByRole("status", { name: /shortcut.*found/i });
    expect(liveStatus).toBeInTheDocument();
    expect(liveStatus).toHaveTextContent("1 shortcut found");

    // Clear search button
    const clearBtn = screen.getByRole("button", { name: "Clear shortcut search filter" });
    expect(clearBtn).toHaveAttribute("title", "Clear search (Esc)");
    fireEvent.click(clearBtn);
    expect(searchInput).toHaveValue("");
    expect(screen.getByText("Show this list")).toBeInTheDocument();

    // Search for unmatched query
    fireEvent.change(searchInput, { target: { value: "nonexistent query" } });
    const emptyState = screen.getByRole("status", { name: 'No shortcuts match "nonexistent query"' });
    expect(emptyState).toBeInTheDocument();

    // Inline clear button in empty state
    const inlineClearBtn = screen.getByRole("button", {
      name: "Clear search filter and show all shortcuts",
    });
    expect(inlineClearBtn).toHaveAttribute("type", "button");
    expect(inlineClearBtn).toHaveAttribute("title", "Clear search filter (Esc)");
    fireEvent.click(inlineClearBtn);
    expect(searchInput).toHaveValue("");
    expect(screen.getByText("Show this list")).toBeInTheDocument();
  });

  it("clears active search query on Escape keypress inside search input without closing overlay", () => {
    const { onClose } = renderShortcutsOverlay();
    const searchInput = screen.getByRole("searchbox", { name: "Filter keyboard shortcuts" });

    fireEvent.change(searchInput, { target: { value: "command" } });
    expect(searchInput).toHaveValue("command");

    fireEvent.keyDown(searchInput, { key: "Escape" });

    expect(searchInput).toHaveValue("");
    expect(onClose).not.toHaveBeenCalled();
  });

  it("announces match count updates to screen readers via polite live region when filtering", () => {
    renderShortcutsOverlay();
    const liveRegion = screen.getByRole("status", { hidden: true });
    expect(liveRegion).toBeInTheDocument();
    expect(liveRegion).toHaveAttribute("aria-live", "polite");
    expect(liveRegion).toHaveTextContent("");

    const searchInput = screen.getByRole("searchbox", { name: "Filter keyboard shortcuts" });

    // Filter down to 1 shortcut ("command")
    fireEvent.change(searchInput, { target: { value: "command" } });
    expect(liveRegion).toHaveTextContent("1 shortcut found");

    // Filter down to 0 shortcuts
    fireEvent.change(searchInput, { target: { value: "nonexistent query" } });
    expect(liveRegion).toHaveTextContent("0 shortcuts found");
  });
});
