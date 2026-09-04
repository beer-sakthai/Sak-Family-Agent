/**
 * Focus behaviour and presentation mode.
 *
 * Both are invisible in a screenshot and load-bearing for anyone driving the
 * dashboard from a keyboard, or reading it from across a room.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import CommandPalette, { type Command } from "@/components/CommandPalette";
import Sidebar from "@/components/shell/Sidebar";
import { usePresentation } from "@/lib/browser-state";
import { focusableWithin } from "@/lib/focus";
import { NAV_ITEMS } from "@/lib/nav";
import { applyPresentation } from "@/lib/theme";

afterEach(() => {
  document.documentElement.removeAttribute("data-presentation");
  window.localStorage.clear();
});

const actions: Command[] = [
  { id: "a", label: "Refresh data", hint: "Re-fetch", group: "Actions", run: vi.fn() },
];

describe("focusableWithin", () => {
  it("finds the controls a Tab would reach, and only those", () => {
    const { container } = render(
      <div>
        <button>one</button>
        <input aria-label="two" />
        <button disabled>skipped</button>
        <span tabIndex={-1}>skipped too</span>
        <a href="#x">three</a>
      </div>,
    );
    const found = focusableWithin(container.firstChild as HTMLElement);
    expect(found.map((element) => element.textContent || element.tagName)).toEqual([
      "one",
      "INPUT",
      "three",
    ]);
  });

  it("skips a subtree hidden from assistive technology", () => {
    const { container } = render(
      <div>
        <button>visible</button>
        <div hidden>
          <button>hidden</button>
        </div>
        <button aria-hidden="true">decorative</button>
      </div>,
    );
    const found = focusableWithin(container.firstChild as HTMLElement);
    expect(found.map((element) => element.textContent)).toEqual(["visible"]);
  });
});

describe("CommandPalette focus", () => {
  function renderPalette() {
    return render(<CommandPalette onClose={vi.fn()} onNavigate={vi.fn()} actions={actions} />);
  }

  it("wraps Tab from the last control back to the first", () => {
    renderPalette();
    const dialog = screen.getByRole("dialog");
    const focusable = focusableWithin(dialog);
    focusable[focusable.length - 1]!.focus();
    fireEvent.keyDown(dialog, { key: "Tab" });
    expect(document.activeElement).toBe(focusable[0]);
  });

  it("wraps Shift+Tab from the first control to the last", () => {
    renderPalette();
    const dialog = screen.getByRole("dialog");
    const focusable = focusableWithin(dialog);
    focusable[0]!.focus();
    fireEvent.keyDown(dialog, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(focusable[focusable.length - 1]);
  });

  it("returns focus to whatever opened it", () => {
    render(<button>opener</button>);
    const opener = screen.getByRole("button", { name: "opener" });
    opener.focus();

    const { unmount } = renderPalette();
    // The palette autofocuses its field, so focus has left the opener.
    expect(document.activeElement).not.toBe(opener);
    unmount();
    expect(document.activeElement).toBe(opener);
  });

  it("jumps option highlighting to start and end with Home and End", () => {
    renderPalette();
    const dialog = screen.getByRole("dialog");
    const options = screen.getAllByRole("option");

    expect(options[0]).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(dialog, { key: "End" });
    expect(options[options.length - 1]).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(dialog, { key: "Home" });
    expect(options[0]).toHaveAttribute("aria-selected", "true");
  });
});

describe("CommandPalette matching", () => {
  it("finds a command from initials rather than a substring", () => {
    render(<CommandPalette onClose={vi.fn()} onNavigate={vi.fn()} actions={actions} />);
    fireEvent.change(screen.getByLabelText("Search commands"), { target: { value: "ovw" } });
    expect(screen.getAllByRole("option")[0]).toHaveTextContent("Overview");
  });

  it("underlines the characters the query matched", () => {
    const { container } = render(
      <CommandPalette onClose={vi.fn()} onNavigate={vi.fn()} actions={actions} />,
    );
    fireEvent.change(screen.getByLabelText("Search commands"), { target: { value: "ovw" } });
    const marks = Array.from(container.querySelectorAll("mark")).map((mark) => mark.textContent);
    expect(marks.join("")).toBe("Ovw");
  });

  it("labels each section row with the digit that reaches it", () => {
    render(<CommandPalette onClose={vi.fn()} onNavigate={vi.fn()} actions={actions} />);
    const rows = screen.getAllByRole("option");
    expect(rows[0]).toHaveTextContent(NAV_ITEMS[0].label);
    expect(rows[0]).toHaveTextContent("1");
  });
});

describe("Sidebar keyboard navigation", () => {
  function renderSidebar(overrides = {}) {
    const props = {
      active: "overview" as const,
      onSelect: vi.fn(),
      collapsed: false,
      onCollapsedChange: vi.fn(),
      counts: {},
      mobileOpen: false,
      onMobileClose: vi.fn(),
      ...overrides,
    };
    return { props, ...render(<Sidebar {...props} />) };
  }

  it("keeps the tablist to a single tab stop", () => {
    renderSidebar({ active: "memory" });
    expect(screen.getByRole("tab", { name: "Memory" })).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("tab", { name: "Overview" })).toHaveAttribute("tabindex", "-1");
  });

  it("moves between sections with the arrow keys", () => {
    const { props } = renderSidebar({ active: "overview" });
    fireEvent.keyDown(screen.getByRole("tablist"), { key: "ArrowDown" });
    expect(props.onSelect).toHaveBeenCalledWith(NAV_ITEMS[1].id);
  });

  it("wraps backwards from the first section to the last", () => {
    const { props } = renderSidebar({ active: "overview" });
    fireEvent.keyDown(screen.getByRole("tablist"), { key: "ArrowUp" });
    expect(props.onSelect).toHaveBeenCalledWith(NAV_ITEMS[NAV_ITEMS.length - 1].id);
  });

  it("jumps to the ends with Home and End", () => {
    const { props } = renderSidebar({ active: "memory" });
    fireEvent.keyDown(screen.getByRole("tablist"), { key: "End" });
    expect(props.onSelect).toHaveBeenCalledWith(NAV_ITEMS[NAV_ITEMS.length - 1].id);
    fireEvent.keyDown(screen.getByRole("tablist"), { key: "Home" });
    expect(props.onSelect).toHaveBeenCalledWith(NAV_ITEMS[0].id);
  });

  it("ignores a key that is not navigation", () => {
    const { props } = renderSidebar();
    fireEvent.keyDown(screen.getByRole("tablist"), { key: "a" });
    expect(props.onSelect).not.toHaveBeenCalled();
  });

  it("marks the column so presentation mode can hide it", () => {
    renderSidebar();
    expect(screen.getByTestId("sidebar")).toHaveAttribute("data-chrome", "sidebar");
  });
});

describe("presentation mode", () => {
  it("sets the attribute the CSS keys off", () => {
    applyPresentation(true, document.documentElement);
    expect(document.documentElement.getAttribute("data-presentation")).toBe("on");
  });

  it("removes the attribute rather than writing a default", () => {
    applyPresentation(true, document.documentElement);
    applyPresentation(false, document.documentElement);
    expect(document.documentElement.hasAttribute("data-presentation")).toBe(false);
  });

  function Probe() {
    const [presenting, setPresenting] = usePresentation();
    return (
      <button onClick={() => setPresenting(!presenting)}>{presenting ? "on" : "off"}</button>
    );
  }

  it("defaults to off and survives a toggle", () => {
    render(<Probe />);
    const button = screen.getByRole("button");
    expect(button).toHaveTextContent("off");
    fireEvent.click(button);
    expect(button).toHaveTextContent("on");
    expect(document.documentElement.getAttribute("data-presentation")).toBe("on");
  });
});
