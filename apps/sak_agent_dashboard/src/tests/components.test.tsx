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
  it("renders headline figures from the metrics payload", () => {
    render(<AnalyticsCharts metrics={demoMetrics()} personas={personas} />);
    expect(screen.getByText(/Total runs:/)).toBeInTheDocument();
  });

  it("shows an em dash rather than a fake success rate with no runs", () => {
    const empty = { ...demoMetrics(), total_runs: 0 };
    render(<AnalyticsCharts metrics={empty} personas={personas} />);
    expect(screen.getByText("—")).toBeInTheDocument();
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

  it("renders an empty state naming the search term", () => {
    renderExplorer({ sessions: [], total: 0, search: "nothing" });
    expect(screen.getByText(/No sessions match/)).toBeInTheDocument();
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
