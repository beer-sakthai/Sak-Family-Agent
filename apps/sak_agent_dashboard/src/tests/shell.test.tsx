/**
 * The application shell: navigation, the KPI strip, the command palette, and
 * the formatting helpers they share.
 *
 * These cover the chrome the panels sit in — which is where a regression is
 * least visible from the payload tests, because none of it renders contract
 * data directly.
 */

import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import CommandPalette, { type Command } from "@/components/CommandPalette";
import HostedNotice from "@/components/HostedNotice";
import KpiStrip from "@/components/KpiStrip";
import { CardGridSkeleton, KpiSkeleton, PanelSkeleton } from "@/components/Skeletons";
import Sidebar from "@/components/shell/Sidebar";
import TopBar from "@/components/shell/TopBar";
import { compactNumber, duration, percent, relativeTime } from "@/lib/format";
import { demoAudit, demoMemory, demoMetrics, demoSessions } from "@/lib/demo";
import { NAV_ITEMS, isTabId, navItem } from "@/lib/nav";

describe("format", () => {
  it("compacts large numbers without losing the magnitude", () => {
    expect(compactNumber(0)).toBe("0");
    expect(compactNumber(999)).toBe("999");
    expect(compactNumber(1_500)).toBe("1.5k");
    expect(compactNumber(84_200)).toBe("84k");
    expect(compactNumber(3_400_000)).toBe("3.4M");
    expect(compactNumber(2_100_000_000)).toBe("2.1B");
  });

  it("returns an em dash rather than NaN for a non-finite figure", () => {
    expect(compactNumber(Number.NaN)).toBe("—");
    expect(duration(Number.NaN)).toBe("—");
    expect(percent(null)).toBe("—");
  });

  it("picks the largest unit a duration reads cleanly in", () => {
    expect(duration(420)).toBe("420ms");
    expect(duration(1_500)).toBe("1.5s");
    expect(duration(125_000)).toBe("2m 5s");
  });

  it("ages a timestamp against an injected clock", () => {
    const now = 1_700_000_000_000;
    expect(relativeTime(now - 1_000, now)).toBe("just now");
    expect(relativeTime(now - 30_000, now)).toBe("30s ago");
    expect(relativeTime(now - 5 * 60_000, now)).toBe("5m ago");
    expect(relativeTime(now - 3 * 3_600_000, now)).toBe("3h ago");
    expect(relativeTime(now - 4 * 86_400_000, now)).toBe("4d ago");
  });
});

describe("nav", () => {
  it("narrows only known section ids", () => {
    expect(isTabId("overview")).toBe(true);
    expect(isTabId("stitch")).toBe(true);
    expect(isTabId("nonsense")).toBe(false);
    expect(isTabId(null)).toBe(false);
  });

  it("resolves every id in the list", () => {
    for (const item of NAV_ITEMS) {
      expect(navItem(item.id).label).toBe(item.label);
    }
  });
});

describe("Sidebar", () => {
  function renderSidebar(overrides = {}) {
    const props = {
      active: "overview" as const,
      onSelect: vi.fn(),
      collapsed: false,
      onCollapsedChange: vi.fn(),
      counts: { sessions: 42 },
      mobileOpen: false,
      onMobileClose: vi.fn(),
      ...overrides,
    };
    return { props, ...render(<Sidebar {...props} />) };
  }

  it("renders one tab per section", () => {
    renderSidebar();
    expect(screen.getAllByRole("tab")).toHaveLength(NAV_ITEMS.length);
  });

  it("marks the active section", () => {
    renderSidebar({ active: "memory" });
    expect(screen.getByRole("tab", { name: "Memory" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "Overview" })).toHaveAttribute("aria-selected", "false");
  });

  it("reports a selection upward", () => {
    const { props } = renderSidebar();
    fireEvent.click(screen.getByRole("tab", { name: "Audit" }));
    expect(props.onSelect).toHaveBeenCalledWith("audit");
  });

  it("shows a count badge only for sections that have one", () => {
    renderSidebar({ counts: { sessions: 42 } });
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(within(screen.getByRole("tab", { name: "Memory" })).queryByText(/\d/)).toBeNull();
  });

  it("hides labels and counts when collapsed", () => {
    renderSidebar({ collapsed: true, counts: { sessions: 42 } });
    // The accessible name survives via aria-label; the visible text does not.
    expect(screen.getByRole("tab", { name: "Sessions" })).toBeInTheDocument();
    expect(screen.queryByText("42")).not.toBeInTheDocument();
  });

  it("toggles collapse through the parent", () => {
    const { props } = renderSidebar({ collapsed: false });
    fireEvent.click(screen.getByLabelText("Collapse sidebar"));
    expect(props.onCollapsedChange).toHaveBeenCalledWith(true);
  });

  it("keeps the mobile drawer unmounted until it is opened", () => {
    const { rerender, props } = renderSidebar({ mobileOpen: false });
    expect(screen.queryByLabelText("Close navigation menu")).not.toBeInTheDocument();
    rerender(<Sidebar {...props} mobileOpen />);
    expect(screen.getByLabelText("Close navigation menu")).toBeInTheDocument();
  });

  it("closes the drawer when a section is chosen inside it", () => {
    const { props } = renderSidebar({ mobileOpen: true });
    // Two copies exist while the drawer is open: the column and the drawer.
    fireEvent.click(screen.getAllByRole("tab", { name: "Workflows" })[0]);
    expect(props.onSelect).toHaveBeenCalledWith("workflows");
    expect(props.onMobileClose).toHaveBeenCalled();
  });
});

describe("TopBar", () => {
  function renderTopBar(overrides = {}) {
    const props = {
      active: "analytics" as const,
      isDemo: false,
      onDemoToggle: vi.fn(),
      activeSource: "local" as const,
      isLoading: false,
      onRefresh: vi.fn(),
      refreshInterval: 0 as const,
      onRefreshIntervalChange: vi.fn(),
      lastUpdatedAt: null,
      now: 1_700_000_000_000,
      onOpenPalette: vi.fn(),
      onOpenMobileNav: vi.fn(),
      ...overrides,
    };
    return { props, ...render(<TopBar {...props} />) };
  }

  it("titles the page after the active section", () => {
    renderTopBar();
    expect(screen.getByRole("heading", { name: "Analytics" })).toBeInTheDocument();
    expect(screen.getByText(navItem("analytics").description)).toBeInTheDocument();
  });

  it("shows how long ago the data was fetched", () => {
    const now = 1_700_000_000_000;
    renderTopBar({ now, lastUpdatedAt: now - 120_000 });
    expect(screen.getByText("2m ago")).toBeInTheDocument();
  });

  it("says Refresh before the first fetch completes", () => {
    renderTopBar({ lastUpdatedAt: null });
    expect(screen.getByText("Refresh")).toBeInTheDocument();
  });

  it("refuses a second refresh while one is in flight", () => {
    const { props } = renderTopBar({ isLoading: true });
    const button = screen.getByLabelText("Refresh dashboard data");
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(props.onRefresh).not.toHaveBeenCalled();
  });

  it("reports an auto-refresh choice as a number", () => {
    const { props } = renderTopBar();
    fireEvent.change(screen.getByLabelText("Auto-refresh interval"), { target: { value: "30" } });
    expect(props.onRefreshIntervalChange).toHaveBeenCalledWith(30);
  });

  it("opens the palette and the mobile nav", () => {
    const { props } = renderTopBar();
    fireEvent.click(screen.getByLabelText("Open command palette"));
    expect(props.onOpenPalette).toHaveBeenCalled();
    fireEvent.click(screen.getByLabelText("Open navigation menu"));
    expect(props.onOpenMobileNav).toHaveBeenCalled();
  });

  it("passes the source badge through to the toggle", () => {
    renderTopBar({ activeSource: "demo" });
    expect(screen.getByTestId("active-source")).toHaveTextContent("Sample data");
  });
});

describe("KpiStrip", () => {
  const metrics = demoMetrics();

  it("renders the headline figures from the payloads", () => {
    render(
      <KpiStrip
        metrics={metrics}
        memory={demoMemory()}
        sessions={demoSessions()}
        audit={demoAudit()}
      />,
    );
    expect(screen.getByText("Total runs")).toBeInTheDocument();
    expect(screen.getByText(metrics.total_runs.toLocaleString())).toBeInTheDocument();
  });

  it("shows em dashes rather than zeroes before anything has loaded", () => {
    render(<KpiStrip metrics={null} memory={null} sessions={null} audit={null} />);
    expect(screen.getAllByText("—").length).toBe(6);
    // Both the run count and the token count say why they are blank.
    expect(screen.getAllByText("no metrics yet")).toHaveLength(2);
  });

  it("declines to rate a run count of zero", () => {
    render(
      <KpiStrip
        metrics={{ ...metrics, total_runs: 0 }}
        memory={null}
        sessions={null}
        audit={null}
      />,
    );
    // The success-rate and latency tiles both decline, for the same reason.
    expect(screen.getAllByText("no runs recorded")).toHaveLength(2);
  });

  it("omits a trend delta when there are too few points to compare", () => {
    render(
      <KpiStrip
        metrics={{ ...metrics, trends: metrics.trends.slice(0, 2) }}
        memory={null}
        sessions={null}
        audit={null}
      />,
    );
    expect(screen.queryAllByTestId("kpi-delta")).toHaveLength(0);
  });

  it("compares the two halves of the trend window when there is enough of it", () => {
    const point = metrics.trends[0];
    render(
      <KpiStrip
        metrics={{
          ...metrics,
          trends: [
            { ...point, runs: 1 },
            { ...point, runs: 1 },
            { ...point, runs: 4 },
            { ...point, runs: 4 },
          ],
        }}
        memory={null}
        sessions={null}
        audit={null}
      />,
    );
    // 2 runs in the older half, 8 in the newer: +300%.
    expect(screen.getByTestId("kpi-delta")).toHaveTextContent("300%");
  });

  it("declines to compute a delta against a window with no runs in it", () => {
    const point = metrics.trends[0];
    render(
      <KpiStrip
        metrics={{ ...metrics, trends: Array.from({ length: 4 }, () => ({ ...point, runs: 0 })) }}
        memory={null}
        sessions={null}
        audit={null}
      />,
    );
    expect(screen.queryAllByTestId("kpi-delta")).toHaveLength(0);
  });

  it("escalates the sessions tile when the audit log has severe events", () => {
    render(
      <KpiStrip
        metrics={metrics}
        memory={null}
        sessions={demoSessions()}
        audit={{ ...demoAudit(), severity_counts: { critical: 2, high: 1 } }}
      />,
    );
    expect(screen.getByText("3 high/critical events")).toBeInTheDocument();
  });
});

describe("CommandPalette", () => {
  const actions: Command[] = [
    { id: "a", label: "Refresh data", hint: "Re-fetch", group: "Actions", run: vi.fn() },
  ];

  function renderPalette(overrides = {}) {
    const props = {
      onClose: vi.fn(),
      onNavigate: vi.fn(),
      actions,
      ...overrides,
    };
    return { props, ...render(<CommandPalette {...props} />) };
  }

  it("lists every section plus the supplied actions", () => {
    renderPalette();
    expect(screen.getAllByRole("option")).toHaveLength(NAV_ITEMS.length + actions.length);
  });

  it("filters on label and on description", () => {
    renderPalette();
    fireEvent.change(screen.getByLabelText("Search commands"), { target: { value: "guardrail" } });
    // Only the Audit section's description mentions the guardrail policy.
    expect(screen.getAllByRole("option")).toHaveLength(1);
    expect(screen.getByRole("option")).toHaveTextContent("Audit");
  });

  it("explains an empty result instead of showing a blank list", () => {
    renderPalette();
    fireEvent.change(screen.getByLabelText("Search commands"), { target: { value: "zzzz" } });
    expect(screen.getByText(/Nothing matches/)).toBeInTheDocument();
  });

  it("navigates on click and closes", () => {
    const { props } = renderPalette();
    fireEvent.click(screen.getByRole("option", { name: /Memory/ }));
    expect(props.onNavigate).toHaveBeenCalledWith("memory");
    expect(props.onClose).toHaveBeenCalled();
  });

  it("moves the highlight with the arrow keys and runs it with Enter", () => {
    const { props } = renderPalette();
    const dialog = screen.getByRole("dialog");
    fireEvent.keyDown(dialog, { key: "ArrowDown" });
    fireEvent.keyDown(dialog, { key: "Enter" });
    expect(props.onNavigate).toHaveBeenCalledWith(NAV_ITEMS[1].id);
  });

  it("wraps the highlight around the top of the list", () => {
    const { props } = renderPalette();
    const dialog = screen.getByRole("dialog");
    fireEvent.keyDown(dialog, { key: "ArrowUp" });
    fireEvent.keyDown(dialog, { key: "Enter" });
    // Last entry is the trailing action, not a section.
    expect(actions[0].run).toHaveBeenCalled();
    expect(props.onNavigate).not.toHaveBeenCalled();
  });

  it("closes on Escape and on the backdrop", () => {
    const { props } = renderPalette();
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
    expect(props.onClose).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByLabelText("Close command palette"));
    expect(props.onClose).toHaveBeenCalledTimes(2);
  });
});

describe("HostedNotice", () => {
  it("explains unrequested sample data", () => {
    render(<HostedNotice activeSource="demo" isDemo={false} />);
    expect(screen.getByTestId("hosted-notice")).toHaveTextContent("SAKTHAI_API_URL");
  });

  it("stays out of the way when the sample data was asked for", () => {
    render(<HostedNotice activeSource="demo" isDemo />);
    expect(screen.queryByTestId("hosted-notice")).not.toBeInTheDocument();
  });

  it("stays out of the way on a live source", () => {
    render(<HostedNotice activeSource="local" isDemo={false} />);
    expect(screen.queryByTestId("hosted-notice")).not.toBeInTheDocument();
  });

  it("says nothing before the first response", () => {
    render(<HostedNotice activeSource={null} isDemo={false} />);
    expect(screen.queryByTestId("hosted-notice")).not.toBeInTheDocument();
  });
});

describe("Skeletons", () => {
  it("holds the KPI layout with one placeholder per tile", () => {
    const { container } = render(<KpiSkeleton />);
    expect(screen.getByTestId("kpi-skeleton").children).toHaveLength(6);
    expect(container.querySelectorAll(".animate-pulse").length).toBe(18);
  });

  it("holds the card grid", () => {
    render(<CardGridSkeleton count={3} />);
    expect(screen.getByTestId("card-grid-skeleton").children).toHaveLength(3);
  });

  it("announces what a panel is loading", () => {
    render(<PanelSkeleton label="Loading sessions" />);
    expect(screen.getByRole("status", { name: "Loading sessions" })).toBeInTheDocument();
  });
});
