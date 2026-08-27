/**
 * Component rendering against contract-shaped data.
 *
 * Every fixture here comes from `lib/demo.ts` — the one demo dataset — so a
 * component that renders in a test renders the same shapes it gets at runtime.
 * Imports are direct: a broken component fails the suite rather than falling
 * through to an inline literal.
 */

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

  it("omits the unattributed badge when there are none", () => {
    render(<AgentOverview personas={{ ...personas, unattributed_runs: 0 }} />);
    expect(screen.queryByText(/unattributed/)).not.toBeInTheDocument();
  });
});

describe("AnalyticsCharts", () => {
  // The headline run/success/latency figures moved to the KPI strip, which is
  // on screen above these charts; see `shell.test.tsx`. What is left here is
  // how much of the family the per-persona charts actually speak for.
  it("says how many personas the per-persona charts are drawn from", () => {
    const attributed = personas.personas.filter((p) => p.runs > 0).length;
    render(<AnalyticsCharts metrics={demoMetrics()} personas={personas} />);
    expect(
      screen.getByText(`${attributed} of ${personas.personas.length} personas have attributed runs`),
    ).toBeInTheDocument();
  });

  it("counts nothing rather than guessing without a personas payload", () => {
    render(<AnalyticsCharts metrics={demoMetrics()} />);
    expect(screen.getByText("0 of 0 personas have attributed runs")).toBeInTheDocument();
  });

  it("renders without a personas payload", () => {
    expect(() => render(<AnalyticsCharts metrics={demoMetrics()} />)).not.toThrow();
  });
});

describe("MemoryExplorer", () => {
  it("shows facts by default", () => {
    render(<MemoryExplorer memory={demoMemory()} />);
    expect(screen.getByText("Prefers a dark, low-contrast terminal")).toBeInTheDocument();
  });

  it("switches to observations", () => {
    render(<MemoryExplorer memory={demoMemory()} />);
    fireEvent.click(screen.getByRole("tab", { name: /Observations/ }));
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

  it("requests a transcript when a row is opened", () => {
    const onSessionSelect = vi.fn();
    renderExplorer({ onSessionSelect });
    fireEvent.click(screen.getAllByText("View")[0]);
    expect(onSessionSelect).toHaveBeenCalledWith(sessions.sessions[0].id);
  });

  it("opens and closes the transcript modal", () => {
    renderExplorer();
    fireEvent.click(screen.getAllByText("View")[0]);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Close transcript"));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("closes the transcript modal when pressing Escape", () => {
    renderExplorer();
    fireEvent.click(screen.getAllByText("View")[0]);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
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
    render(<WorkflowRuns runs={workflows.runs} onRunSelect={vi.fn()} detail={null} />);
    expect(screen.getByText("nightly-consolidation")).toBeInTheDocument();
    expect(screen.getAllByText("completed").length).toBeGreaterThan(0);
  });

  it("marks failed steps", () => {
    render(<WorkflowRuns runs={workflows.runs} onRunSelect={vi.fn()} detail={null} />);
    expect(screen.getByText("(1 failed)")).toBeInTheDocument();
  });

  it("requests detail when a run is opened", () => {
    const onRunSelect = vi.fn();
    render(<WorkflowRuns runs={workflows.runs} onRunSelect={onRunSelect} detail={null} />);
    // By role, not by text: the table's own column header is also "Steps".
    fireEvent.click(screen.getAllByRole("button", { name: "Steps" })[0]);
    expect(onRunSelect).toHaveBeenCalledWith(workflows.runs[0].run_id);
  });

  it("shows step detail in the modal", () => {
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
    render(<WorkflowRuns runs={workflows.runs} onRunSelect={vi.fn()} detail={detail} />);
    fireEvent.click(screen.getAllByRole("button", { name: "Steps" })[0]);
    expect(screen.getByText("fetch")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
    expect(screen.getByText("3 attempts")).toBeInTheDocument();
  });

  it("closes the steps modal when pressing Escape", () => {
    render(<WorkflowRuns runs={workflows.runs} onRunSelect={vi.fn()} detail={null} />);
    fireEvent.click(screen.getAllByRole("button", { name: "Steps" })[0]);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders an empty state", () => {
    render(<WorkflowRuns runs={[]} onRunSelect={vi.fn()} detail={null} />);
    expect(screen.getByText("No workflow runs recorded yet.")).toBeInTheDocument();
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
