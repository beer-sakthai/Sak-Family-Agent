/**
 * Component rendering against contract-shaped data.
 *
 * Every fixture here comes from `lib/demo.ts` — the one demo dataset — so a
 * component that renders in a test renders the same shapes it gets at runtime.
 * Imports are direct: a broken component fails the suite rather than falling
 * through to an inline literal.
 */

import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import AgentCard from "@/components/AgentCard";
import AgentOverview from "@/components/AgentOverview";
import AnalyticsCharts from "@/components/AnalyticsCharts";
import AuditLogs from "@/components/AuditLogs";
import DemoModeToggle from "@/components/DemoModeToggle";
import MemoryExplorer from "@/components/MemoryExplorer";
import SessionExplorer from "@/components/SessionExplorer";
import WorkflowRuns from "@/components/WorkflowRuns";
import type { PersonaSummary } from "@/lib/contracts.generated";
import {
  demoAudit,
  demoMemory,
  demoMetrics,
  demoPersonas,
  demoSessions,
  demoWorkflows,
} from "@/lib/demo";
import { TREND_WINDOWS, trendWindowLabel } from "@/lib/url-state";

const personas = demoPersonas();
const active = personas.personas.find((p) => p.runs > 0)!;
const idle = personas.personas.find((p) => p.runs === 0)!;

describe("AgentCard", () => {
  it("renders the persona's display name", () => {
    render(<AgentCard agent={active} />);
    expect(screen.getByText(active.display_name)).toBeInTheDocument();
  });

  it("shows a computed success rate, not a hardcoded score", () => {
    const agent: PersonaSummary = { ...active, runs: 10, errors: 2 };
    render(<AgentCard agent={agent} />);
    expect(screen.getByText("80.0%")).toBeInTheDocument();
  });

  it("says so when a persona has no runs instead of inventing a score", () => {
    render(<AgentCard agent={idle} />);
    expect(screen.getByText("no runs yet")).toBeInTheDocument();
  });

  it("labels a persona with no shard as Idle", () => {
    render(<AgentCard agent={idle} />);
    expect(screen.getByText("Idle")).toBeInTheDocument();
  });

  it("reports a missing memory shard plainly", () => {
    render(<AgentCard agent={idle} />);
    expect(screen.getByText("no memory shard yet")).toBeInTheDocument();
  });

  it("renders identically across repeated renders", () => {
    // The previous card filled a missing score with Math.random().
    const first = render(<AgentCard agent={active} />).container.innerHTML;
    const second = render(<AgentCard agent={active} />).container.innerHTML;
    expect(first).toBe(second);
  });

  it("stays a single toggle button when there is no detail to open", () => {
    // The overlay/details split only exists once a card has two things to do.
    render(<AgentCard agent={active} onToggle={vi.fn()} selected={false} />);
    expect(
      screen.getByRole("button", { name: `Add ${active.display_name} to the persona filter` }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Open details/ })).not.toBeInTheDocument();
  });

  it("offers both the filter toggle and a details control without nesting them", () => {
    const { container } = render(
      <AgentCard agent={active} onToggle={vi.fn()} onOpenDetail={vi.fn()} selected={false} />,
    );
    expect(
      screen.getByRole("button", { name: `Add ${active.display_name} to the persona filter` }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: `Open details for ${active.display_name}` }),
    ).toBeInTheDocument();
    // A <button> inside a <button> is invalid, and browsers resolve it by
    // dropping one of the two controls.
    expect(container.querySelector("button button")).toBeNull();
  });

  it("reports the two controls separately", () => {
    const onToggle = vi.fn();
    const onOpenDetail = vi.fn();
    render(<AgentCard agent={active} onToggle={onToggle} onOpenDetail={onOpenDetail} />);

    fireEvent.click(screen.getByRole("button", { name: `Open details for ${active.display_name}` }));
    expect(onOpenDetail).toHaveBeenCalledTimes(1);
    expect(onToggle).not.toHaveBeenCalled();

    fireEvent.click(
      screen.getByRole("button", { name: `Add ${active.display_name} to the persona filter` }),
    );
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it("marks the overlay toggle pressed for a selected persona", () => {
    render(<AgentCard agent={active} onToggle={vi.fn()} onOpenDetail={vi.fn()} selected />);
    expect(
      screen.getByRole("button", {
        name: `Remove ${active.display_name} from the persona filter`,
      }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("shows an error count only when there are errors", () => {
    const { rerender } = render(<AgentCard agent={{ ...active, errors: 0 }} />);
    expect(screen.queryByText(/error/)).not.toBeInTheDocument();
    rerender(<AgentCard agent={{ ...active, errors: 3 }} />);
    expect(screen.getByText("3 errors")).toBeInTheDocument();
  });
});

describe("AgentOverview", () => {
  it("renders a card for all six personas", () => {
    render(<AgentOverview personas={personas} />);
    expect(screen.getByText("6 Personas Registered")).toBeInTheDocument();
  });

  it("surfaces unattributed runs rather than hiding them", () => {
    render(<AgentOverview personas={personas} />);
    expect(screen.getByText(`${personas.unattributed_runs} unattributed`)).toBeInTheDocument();
  });

  it("draws the activity calendar only once there is a trend series", () => {
    const { queryByTestId } = render(<AgentOverview personas={personas} />);
    expect(queryByTestId("activity-heatmap")).toBeNull();

    render(<AgentOverview personas={personas} trends={demoMetrics().trends} />);
    expect(screen.getByTestId("activity-heatmap")).toBeInTheDocument();
  });

  it("passes the persona name up when a card's details are opened", () => {
    const onOpenDetail = vi.fn();
    render(<AgentOverview personas={personas} onOpenDetail={onOpenDetail} />);
    fireEvent.click(screen.getByRole("button", { name: `Open details for ${active.display_name}` }));
    expect(onOpenDetail).toHaveBeenCalledWith(active.name);
  });

  it("omits the unattributed badge when there are none", () => {
    render(<AgentOverview personas={{ ...personas, unattributed_runs: 0 }} />);
    expect(screen.queryByText(/unattributed/)).not.toBeInTheDocument();
  });
});

describe("AnalyticsCharts", () => {
  // The scope pill now carries the trend length as well as the persona count,
  // so it is asked for by test id rather than by its full sentence.
  function renderCharts(props: Partial<React.ComponentProps<typeof AnalyticsCharts>> = {}) {
    return render(
      <AnalyticsCharts
        metrics={demoMetrics()}
        trend={30}
        onTrendChange={vi.fn()}
        {...props}
      />,
    );
  }

  // The headline run/success/latency figures moved to the KPI strip, which is
  // on screen above these charts; see `shell.test.tsx`. What is left here is
  // how much of the family the per-persona charts actually speak for.
  it("says how many personas the per-persona charts are drawn from", () => {
    const attributed = personas.personas.filter((p) => p.runs > 0).length;
    renderCharts({ personas });
    expect(screen.getByTestId("analytics-scope")).toHaveTextContent(
      `${attributed} of ${personas.personas.length} personas have attributed runs`,
    );
  });

  it("counts nothing rather than guessing without a personas payload", () => {
    renderCharts();
    expect(screen.getByTestId("analytics-scope")).toHaveTextContent(
      "0 of 0 personas have attributed runs",
    );
  });

  it("renders without a personas payload", () => {
    expect(() => renderCharts()).not.toThrow();
  });

  it("draws only the last N days for a narrowed window", () => {
    renderCharts({ trend: 7 });
    const expected = Math.min(7, demoMetrics().trends.length);
    expect(screen.getByTestId("analytics-scope")).toHaveTextContent(`${expected} days of trend`);
  });

  it("draws every recorded day for the all-history window", () => {
    renderCharts({ trend: 0 });
    expect(screen.getByTestId("analytics-scope")).toHaveTextContent(
      `${demoMetrics().trends.length} days of trend`,
    );
  });

  it("marks the active window and reports a change upward", () => {
    const onTrendChange = vi.fn();
    renderCharts({ trend: 30, onTrendChange });
    expect(screen.getByRole("button", { name: "30d" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "7d" }));
    expect(onTrendChange).toHaveBeenCalledWith(7);
  });

  it("offers every window the URL can carry", () => {
    renderCharts();
    for (const days of TREND_WINDOWS) {
      expect(
        screen.getByRole("button", { name: trendWindowLabel(days) }),
      ).toBeInTheDocument();
    }
  });
});

describe("MemoryExplorer", () => {
  // Two tablists can share a page, so the role alone does not identify this
  // one to a screen reader.
  it("names its tablist for assistive tech", () => {
    render(<MemoryExplorer memory={demoMemory()} />);
    expect(screen.getByRole("tablist", { name: "Memory Explorer tabs" })).toBeInTheDocument();
  });

  it("applies offset focus ring styles on tabs for keyboard accessibility", () => {
    render(<MemoryExplorer memory={demoMemory()} />);
    const factsTab = screen.getByRole("tab", { name: /Facts/ });
    expect(factsTab.className).toContain("focus-visible:ring-offset-2");
    expect(factsTab.className).toContain("focus-visible:ring-offset-canvas");
  });

  it("uses roving tabIndex for active and inactive tabs", () => {
    render(<MemoryExplorer memory={demoMemory()} />);
    const factsTab = screen.getByRole("tab", { name: /Facts/ });
    const obsTab = screen.getByRole("tab", { name: /Observations/ });
    expect(factsTab).toHaveAttribute("tabIndex", "0");
    expect(obsTab).toHaveAttribute("tabIndex", "-1");

    fireEvent.click(obsTab);
    expect(factsTab).toHaveAttribute("tabIndex", "-1");
    expect(obsTab).toHaveAttribute("tabIndex", "0");
  });

  it("supports keyboard arrow and home/end navigation between tabs", () => {
    render(<MemoryExplorer memory={demoMemory()} />);
    const tablist = screen.getByRole("tablist", { name: "Memory Explorer tabs" });
    const factsTab = screen.getByRole("tab", { name: /Facts/ });
    const obsTab = screen.getByRole("tab", { name: /Observations/ });

    fireEvent.keyDown(tablist, { key: "ArrowRight" });
    expect(obsTab).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(tablist, { key: "ArrowLeft" });
    expect(factsTab).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(tablist, { key: "End" });
    expect(obsTab).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(tablist, { key: "Home" });
    expect(factsTab).toHaveAttribute("aria-selected", "true");
  });

  it("shows facts by default", () => {
    render(<MemoryExplorer memory={demoMemory()} />);
    expect(screen.getByText("Prefers a dark, low-contrast terminal")).toBeInTheDocument();
  });

  it("switches to observations and links tabpanel to tab", () => {
    render(<MemoryExplorer memory={demoMemory()} />);
    expect(screen.getByRole("tabpanel", { name: /Facts/ })).toHaveAttribute("id", "panel-facts");
    const obsTab = screen.getByRole("tab", { name: /Observations/ });
    expect(obsTab).toHaveAttribute("aria-controls", "panel-observations");
    fireEvent.click(obsTab);
    expect(screen.getByRole("tabpanel", { name: /Observations/ })).toHaveAttribute(
      "id",
      "panel-observations",
    );
    expect(screen.getByText("Works late into the evening most days")).toBeInTheDocument();
  });

  it("tags each fact with its shard", () => {
    render(<MemoryExplorer memory={demoMemory()} />);
    expect(screen.getAllByText("sakthai").length).toBeGreaterThan(0);
  });

  it("renders an empty state", () => {
    const empty = { ...demoMemory(), facts: [] };
    render(<MemoryExplorer memory={empty} />);
    expect(screen.getByText("No memory facts found.")).toBeInTheDocument();
  });

  it("sets tabIndex=0 on the active tab and tabIndex=-1 on inactive tabs", () => {
    render(<MemoryExplorer memory={demoMemory()} />);
    const factsTab = screen.getByRole("tab", { name: /Facts/ });
    const obsTab = screen.getByRole("tab", { name: /Observations/ });

    expect(factsTab).toHaveAttribute("tabindex", "0");
    expect(obsTab).toHaveAttribute("tabindex", "-1");

    fireEvent.click(obsTab);

    expect(factsTab).toHaveAttribute("tabindex", "-1");
    expect(obsTab).toHaveAttribute("tabindex", "0");
  });

  it("navigates tabs using Arrow keys and Home/End keys", () => {
    render(<MemoryExplorer memory={demoMemory()} />);
    const factsTab = screen.getByRole("tab", { name: /Facts/ });
    const obsTab = screen.getByRole("tab", { name: /Observations/ });

    fireEvent.keyDown(factsTab, { key: "ArrowRight" });
    expect(obsTab).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(obsTab, { key: "ArrowLeft" });
    expect(factsTab).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(factsTab, { key: "End" });
    expect(obsTab).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(obsTab, { key: "Home" });
    expect(factsTab).toHaveAttribute("aria-selected", "true");
  });
});

describe("AuditLogs", () => {
  it("renders events", () => {
    render(<AuditLogs audit={demoAudit()} severity="ALL" onSeverityChange={vi.fn()} />);
    expect(screen.getByText("Blocked a destructive shell command")).toBeInTheDocument();
  });

  it("reports the filter upward instead of filtering locally", () => {
    const onChange = vi.fn();
    render(<AuditLogs audit={demoAudit()} severity="ALL" onSeverityChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: /critical severity/ }));
    expect(onChange).toHaveBeenCalledWith("critical");
  });

  it("marks the active severity", () => {
    render(<AuditLogs audit={demoAudit()} severity="high" onSeverityChange={vi.fn()} />);
    expect(screen.getByRole("button", { name: /high severity/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("explains an empty log rather than looking broken", () => {
    const empty = { events: [], severity_counts: {}, total: 0 };
    render(<AuditLogs audit={empty} severity="ALL" onSeverityChange={vi.fn()} />);
    expect(screen.getByText(/An empty audit log is a normal state/)).toBeInTheDocument();
  });
});

describe("SessionExplorer", () => {
  const sessions = demoSessions();

  function renderExplorer(overrides = {}) {
    return render(
      <SessionExplorer
        sessions={sessions.sessions}
        total={sessions.total}
        search=""
        onSearchChange={vi.fn()}
        page={1}
        pageSize={10}
        onPageChange={vi.fn()}
        onSessionSelect={vi.fn()}
        openSessionId={null}
        detail={null}
        {...overrides}
      />,
    );
  }

  it("lists sessions", () => {
    renderExplorer();
    expect(screen.getByText("Draft the release notes for v2.1")).toBeInTheDocument();
  });

  it("labels an unattributed session as such", () => {
    renderExplorer();
    expect(screen.getAllByText("unattributed").length).toBeGreaterThan(0);
  });

  it("sends search upward for a server-side query", () => {
    const onSearchChange = vi.fn();
    renderExplorer({ onSearchChange });
    fireEvent.change(screen.getByLabelText("Search sessions"), { target: { value: "deploy" } });
    expect(onSearchChange).toHaveBeenCalledWith("deploy");
  });

  it("requests a transcript when a row is opened and has accessible aria-label", () => {
    const onSessionSelect = vi.fn();
    renderExplorer({ onSessionSelect });
    const viewButton = screen.getByRole("button", {
      name: `View transcript for task "${sessions.sessions[0].task}"`,
    });
    expect(viewButton).toBeInTheDocument();
    fireEvent.click(viewButton);
    expect(onSessionSelect).toHaveBeenCalledWith(sessions.sessions[0].id);
  });

  it("provides descriptive aria-labels on action buttons for screen readers", () => {
    renderExplorer();
    const firstSession = sessions.sessions[0];
    const expectedLabel = `View transcript for task "${firstSession.task}"`;
    expect(screen.getByRole("button", { name: expectedLabel })).toBeInTheDocument();
  });

  // The open transcript now lives in the URL, so the page owns it: the panel
  // renders the drawer when told to and reports a close upward rather than
  // opening and closing itself.
  it("renders no drawer when nothing is open", () => {
    renderExplorer({ openSessionId: null });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders the drawer for the open session id", () => {
    renderExplorer({ openSessionId: sessions.sessions[0].id });
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByTestId("session-drawer")).toBeInTheDocument();
  });

  it("reports a close upward instead of closing itself", () => {
    const onSessionSelect = vi.fn();
    renderExplorer({ openSessionId: sessions.sessions[0].id, onSessionSelect });
    fireEvent.click(screen.getByLabelText("Close detail panel"));
    expect(onSessionSelect).toHaveBeenCalledWith(null);
  });

  it("closes the drawer on Escape", () => {
    const onSessionSelect = vi.fn();
    renderExplorer({ openSessionId: sessions.sessions[0].id, onSessionSelect });
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onSessionSelect).toHaveBeenCalledWith(null);
  });

  it("renders an empty state naming the search term", () => {
    renderExplorer({ sessions: [], total: 0, search: "nothing" });
    expect(screen.getByText(/No sessions match/)).toBeInTheDocument();
  });

  // Ported from main (6f6ef8d, f2b0d71): a clear-search affordance and an
  // empty-state reset. Adapted because search is server-driven here, so both
  // report upward rather than mutating local state.
  it("offers a clear-search button only once there is a query", () => {
    const { rerender } = renderExplorer({ search: "" });
    expect(screen.queryByLabelText("Clear search query")).not.toBeInTheDocument();
    rerender(
      <SessionExplorer
        sessions={sessions.sessions}
        total={sessions.total}
        search="deploy"
        onSearchChange={vi.fn()}
        page={1}
        pageSize={10}
        onPageChange={vi.fn()}
        onSessionSelect={vi.fn()}
        openSessionId={null}
        detail={null}
      />,
    );
    expect(screen.getByLabelText("Clear search query")).toBeInTheDocument();
  });

  it("clears the query through the parent when the button is used", () => {
    const onSearchChange = vi.fn();
    renderExplorer({ search: "deploy", onSearchChange });
    fireEvent.click(screen.getByLabelText("Clear search query"));
    expect(onSearchChange).toHaveBeenCalledWith("");
  });

  it("offers a reset action from the empty state", () => {
    const onSearchChange = vi.fn();
    renderExplorer({ sessions: [], total: 0, search: "nothing", onSearchChange });
    fireEvent.click(screen.getByRole("button", { name: /Clear search and filters/i }));
    expect(onSearchChange).toHaveBeenCalledWith("");
  });

  // Ported from PR #1180, rewritten against the server-driven props: the
  // original asserted on a `currentPage` state this component no longer owns.
  it("says which end of the list a disabled pagination button is at", () => {
    renderExplorer({ total: 25, page: 1 });
    expect(screen.getByLabelText("Previous page")).toHaveAttribute("title", "First page reached");
    expect(screen.getByLabelText("Next page")).toHaveAttribute("title", "Next page");
  });

  it("names the action on a pagination button that is still usable", () => {
    renderExplorer({ total: 25, page: 3 });
    expect(screen.getByLabelText("Previous page")).toHaveAttribute("title", "Previous page");
    expect(screen.getByLabelText("Next page")).toHaveAttribute("title", "Last page reached");
  });

  it("shows no reset action when the list is empty for lack of data", () => {
    renderExplorer({ sessions: [], total: 0, search: "" });
    expect(screen.getByText("No sessions recorded yet.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Clear search/i })).not.toBeInTheDocument();
  });
});

describe("WorkflowRuns", () => {
  const workflows = demoWorkflows();

  it("lists runs with their status", () => {
    render(<WorkflowRuns runs={workflows.runs} onRunSelect={vi.fn()} openRunId={null} detail={null} />);
    expect(screen.getByText("nightly-consolidation")).toBeInTheDocument();
    expect(screen.getAllByText("completed").length).toBeGreaterThan(0);
  });

  it("marks failed steps", () => {
    render(<WorkflowRuns runs={workflows.runs} onRunSelect={vi.fn()} openRunId={null} detail={null} />);
    expect(screen.getByText("(1 failed)")).toBeInTheDocument();
  });

  it("requests detail when a run is opened", () => {
    const onRunSelect = vi.fn();
    render(<WorkflowRuns runs={workflows.runs} onRunSelect={onRunSelect} openRunId={null} detail={null} />);
    const expectedLabel = `View steps for ${workflows.runs[0].workflow_name || workflows.runs[0].run_id}`;
    fireEvent.click(screen.getByRole("button", { name: expectedLabel }));
    expect(onRunSelect).toHaveBeenCalledWith(workflows.runs[0].run_id);
  });

  it("shows step detail in the drawer", () => {
    const detail = {
      summary: workflows.runs[0],
      steps: [
        {
          step_id: "fetch",
          status: "failed",
          attempts: 3,
          error: "boom",
          started_at: null,
          finished_at: null,
          duration_seconds: null,
        },
      ],
    };
    render(
      <WorkflowRuns
        runs={workflows.runs}
        onRunSelect={vi.fn()}
        openRunId={workflows.runs[0].run_id}
        detail={detail}
      />,
    );
    expect(screen.getByText("fetch")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
    expect(screen.getByText("3 attempts")).toBeInTheDocument();
  });

  it("renders an empty state", () => {
    render(<WorkflowRuns runs={[]} onRunSelect={vi.fn()} openRunId={null} detail={null} />);
    expect(screen.getByText("No workflow runs recorded yet.")).toBeInTheDocument();
  });

  // Workflow runs record no persona, so this panel cannot honour the global
  // filter — and must not let the topbar's filter imply that it did.
  it("says so when a persona filter it cannot honour is active", () => {
    render(
      <WorkflowRuns
        runs={workflows.runs}
        onRunSelect={vi.fn()}
        openRunId={null}
        familyWide
        detail={null}
      />,
    );
    expect(screen.getByTestId("workflows-family-wide")).toBeInTheDocument();
  });

  it("stays quiet when no filter is active", () => {
    render(
      <WorkflowRuns runs={workflows.runs} onRunSelect={vi.fn()} openRunId={null} detail={null} />,
    );
    expect(screen.queryByTestId("workflows-family-wide")).not.toBeInTheDocument();
  });
});

describe("DemoModeToggle", () => {
  it("reports the source actually in use", () => {
    render(<DemoModeToggle isDemo={false} onToggle={vi.fn()} activeSource="local" />);
    expect(screen.getByTestId("active-source")).toHaveTextContent("Live · local ~/.sakthai");
  });

  it("can report demo even while the toggle is off", () => {
    // The honest case: live data was requested but no runtime exists.
    render(<DemoModeToggle isDemo={false} onToggle={vi.fn()} activeSource="demo" />);
    expect(screen.getByTestId("active-source")).toHaveTextContent("Sample data");
    expect(screen.getByRole("button", { name: /Toggle sample data/ })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("distinguishes the API source", () => {
    render(<DemoModeToggle isDemo={false} onToggle={vi.fn()} activeSource="api" />);
    expect(screen.getByTestId("active-source")).toHaveTextContent("Live · SakThai API");
  });

  it("toggles", () => {
    const onToggle = vi.fn();
    render(<DemoModeToggle isDemo={false} onToggle={onToggle} activeSource="local" />);
    fireEvent.click(screen.getByRole("button", { name: /Toggle sample data/ }));
    expect(onToggle).toHaveBeenCalledWith(true);
  });

  it("omits the badge before the first response", () => {
    render(<DemoModeToggle isDemo={false} onToggle={vi.fn()} activeSource={null} />);
    expect(screen.queryByTestId("active-source")).not.toBeInTheDocument();
  });
});
