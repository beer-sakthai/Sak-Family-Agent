import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import Home from "@/app/page";
import DemoModeToggle from "@/components/DemoModeToggle";
import SessionExplorer from "@/components/SessionExplorer";
import AnalyticsCharts from "@/components/AnalyticsCharts";
import MemoryExplorer from "@/components/MemoryExplorer";
import AuditLogs from "@/components/AuditLogs";
import { SessionMeta, SessionTranscript, MetricsData, AgentPersona } from "@/lib/types";

describe("Empirical UI Stress & Interactive Verification Suite", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("1. Demo Mode Toggle Transitions & Latency", () => {
    it("toggles state between Real and Demo mode and triggers telemetry refetch", async () => {
      const handleToggle = vi.fn();
      const { rerender } = render(<DemoModeToggle isDemo={false} onToggle={handleToggle} />);

      // Verify OFF state labels
      expect(screen.getByText(/Demo Mode: OFF/i)).toBeInTheDocument();
      expect(screen.getByText("Live Runtime")).toBeInTheDocument();

      // Click toggle
      const toggleBtn = screen.getByRole("button");
      fireEvent.click(toggleBtn);
      expect(handleToggle).toHaveBeenCalledWith(true);

      // Rerender with isDemo = true
      rerender(<DemoModeToggle isDemo={true} onToggle={handleToggle} />);
      expect(screen.getByText(/Demo Mode: ON/i)).toBeInTheDocument();
      expect(screen.getByText("Sample Data")).toBeInTheDocument();
    });

    it("stress tests rapid toggling (50 cycles) without state desynchronization", () => {
      let isDemoState = false;
      const handleToggle = vi.fn((val) => {
        isDemoState = typeof val === "boolean" ? val : !isDemoState;
      });

      const { rerender } = render(<DemoModeToggle isDemo={isDemoState} onToggle={handleToggle} />);

      for (let i = 0; i < 50; i++) {
        const toggleBtn = screen.getByRole("button");
        fireEvent.click(toggleBtn);
        rerender(<DemoModeToggle isDemo={isDemoState} onToggle={handleToggle} />);
      }

      expect(handleToggle).toHaveBeenCalledTimes(50);
      expect(isDemoState).toBe(false); // 50 toggles from false -> false
    });

    it("verifies home page demo mode state switch triggers fetch with demo query param", async () => {
      const mockFetch = vi.fn().mockImplementation((url: string) => {
        return Promise.resolve({
          ok: true,
          json: () => {
            if (url.includes("/api/agents")) return Promise.resolve({ success: true, agents: [] });
            if (url.includes("/api/metrics")) return Promise.resolve({ success: true, metrics: {} });
            if (url.includes("/api/memory")) return Promise.resolve({ success: true, memory: { facts: [], observations: [] }, auditLogs: [] });
            if (url.includes("/api/sessions")) return Promise.resolve({ success: true, sessions: [], total: 0 });
            return Promise.resolve({ success: true });
          },
        });
      });
      global.fetch = mockFetch;

      render(<Home />);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      });

      // Verify initial fetch uses demo=false
      const initialCalls = mockFetch.mock.calls.map((c) => c[0] as string);
      expect(initialCalls.some((url) => url.includes("demo=false"))).toBe(true);

      // Click Demo Mode toggle in header
      const toggleBtn = screen.getByRole("button", { name: /Demo Mode/i });
      fireEvent.click(toggleBtn);

      await waitFor(() => {
        const demoCalls = mockFetch.mock.calls.map((c) => c[0] as string);
        expect(demoCalls.some((url) => url.includes("demo=true"))).toBe(true);
      });
    });
  });

  describe("2. Search Filtering Latency & Performance", () => {
    it("measures search filtering latency on large dataset (10,000 session items)", () => {
      const largeSessionSet: SessionMeta[] = Array.from({ length: 10000 }, (_, i) => ({
        sessionId: `sess-large-${i + 1}`,
        persona: i % 5 === 0 ? "SakThai" : i % 5 === 1 ? "SakKing" : i % 5 === 2 ? "SakSee" : i % 5 === 3 ? "SakSit" : "SakJules",
        timestamp: "2026-08-02T12:00:00Z",
        messageCount: (i % 15) + 1,
        tokenUsage: (i * 10) + 100,
        status: i % 20 === 0 ? "failed" : "completed",
      }));

      const startTime = performance.now();
      render(<SessionExplorer sessions={largeSessionSet} total={10000} />);
      const renderTime = performance.now() - startTime;

      // Ensure initial render takes under 3000ms in synthetic test runner environment
      expect(renderTime).toBeLessThan(3000);

      const searchInput = screen.getByPlaceholderText(/search sessions/i);

      const filterStartTime = performance.now();
      fireEvent.change(searchInput, { target: { value: "SakKing" } });
      const filterDuration = performance.now() - filterStartTime;

      // Filtering 10,000 items in React JS DOM should complete under 2000ms in test environment
      expect(filterDuration).toBeLessThan(2000);

      // Confirm matching session items rendered
      expect(screen.getByText("sess-large-2")).toBeInTheDocument();
      expect(screen.queryByText("sess-large-1")).not.toBeInTheDocument();
    });

    it("verifies status filter and persona dropdown combinations execute cleanly", () => {
      const sampleSessions: SessionMeta[] = [
        { sessionId: "s-1", persona: "SakThai", timestamp: "2026-08-02", messageCount: 2, tokenUsage: 500, status: "completed" },
        { sessionId: "s-2", persona: "SakKing", timestamp: "2026-08-02", messageCount: 4, tokenUsage: 1200, status: "failed" },
        { sessionId: "s-3", persona: "SakThai", timestamp: "2026-08-02", messageCount: 6, tokenUsage: 2200, status: "failed" },
      ];

      render(<SessionExplorer sessions={sampleSessions} total={3} />);

      const selects = screen.getAllByRole("combobox");
      const personaSelect = selects[0];
      const statusSelect = selects[1];

      // Filter SakThai + failed
      fireEvent.change(personaSelect, { target: { value: "SakThai" } });
      fireEvent.change(statusSelect, { target: { value: "failed" } });

      expect(screen.getByText("s-3")).toBeInTheDocument();
      expect(screen.queryByText("s-1")).not.toBeInTheDocument();
      expect(screen.queryByText("s-2")).not.toBeInTheDocument();
    });
  });

  describe("3. Modal Transcript Popup Behavior", () => {
    it("opens inspect modal on button click, displays transcript metadata & closes cleanly", async () => {
      const mockOnSelect = vi.fn();
      const mockSessions: SessionMeta[] = [
        { sessionId: "sess-inspect-100", persona: "SakSit", timestamp: "2026-08-02T14:00:00Z", messageCount: 3, tokenUsage: 850, status: "completed" },
      ];

      const mockDetail: SessionTranscript = {
        sessionId: "sess-inspect-100",
        persona: "SakSit",
        timestamp: "2026-08-02T14:00:00Z",
        messageCount: 3,
        tokenUsage: 850,
        status: "completed",
        task: "Audit security policy compliance",
        model: "saksit-v1-auditor",
        messages: [
          { role: "user", content: "Run security audit on network ingress", timestamp: "2026-08-02T14:00:01Z" },
          { role: "assistant", content: "Ingress security check passed with 0 flags.", timestamp: "2026-08-02T14:00:02Z" },
        ],
        result: { status: "OK", score: 100 },
      };

      const { rerender } = render(
        <SessionExplorer
          sessions={mockSessions}
          total={1}
          onSessionSelect={mockOnSelect}
          selectedSessionDetail={null}
        />
      );

      // Verify inspect modal is initially closed
      expect(screen.queryByText("Session Transcript Detail")).not.toBeInTheDocument();

      // Click inspect button
      const inspectBtn = screen.getByRole("button", { name: /Inspect/i });
      fireEvent.click(inspectBtn);

      expect(mockOnSelect).toHaveBeenCalledWith("sess-inspect-100");

      // Rerender with selectedSessionDetail populated
      rerender(
        <SessionExplorer
          sessions={mockSessions}
          total={1}
          onSessionSelect={mockOnSelect}
          selectedSessionDetail={mockDetail}
        />
      );

      // Verify modal content
      expect(screen.getByText("Session Transcript Detail")).toBeInTheDocument();
      expect(screen.getByText("Audit security policy compliance")).toBeInTheDocument();
      expect(screen.getByText("Run security audit on network ingress")).toBeInTheDocument();
      expect(screen.getByText("Ingress security check passed with 0 flags.")).toBeInTheDocument();

      // Close modal
      const closeBtn = screen.getByRole("button", { name: /Close Inspector/i });
      fireEvent.click(closeBtn);

      // Verify modal unmounts
      expect(screen.queryByText("Session Transcript Detail")).not.toBeInTheDocument();
    });
  });

  describe("4. Tab Switching & Shell Navigation", () => {
    it("switches tabs smoothly between Overview, Analytics, Sessions, and Memory", () => {
      render(<Home />);

      // Default active tab is overview
      expect(screen.getByText("Sak-Agent-Family Personas")).toBeInTheDocument();

      // Click Analytics tab
      const analyticsTab = screen.getByRole("button", { name: /Analytics & Charts/i });
      fireEvent.click(analyticsTab);

      expect(screen.getByText("Performance & Benchmark Analytics")).toBeInTheDocument();
      expect(screen.queryByText("Sak-Agent-Family Personas")).not.toBeInTheDocument();

      // Click Sessions tab
      const sessionsTab = screen.getByRole("button", { name: /Session Explorer/i });
      fireEvent.click(sessionsTab);

      expect(screen.getByText("Session History & Transcript Explorer")).toBeInTheDocument();

      // Click Memory tab
      const memoryTab = screen.getByRole("button", { name: /Memory & Security Logs/i });
      fireEvent.click(memoryTab);

      expect(screen.getByText(/SQLite Memory Store Explorer/i)).toBeInTheDocument();
      expect(screen.getByText(/Security Audit Log Inspector/i)).toBeInTheDocument();
    });
  });

  describe("5. Chart Responsiveness & Extreme Dataset Resilience", () => {
    it("renders AnalyticsCharts without throwing when metrics object contains zero or missing stats", () => {
      const emptyMetrics: MetricsData = {
        totalRuns: 0,
        avgLatencyMs: 0,
        successRate: 0,
        tokenStats: { totalTokens: 0, promptTokens: 0, completionTokens: 0 },
        stopReasons: {},
        trends: [],
      };

      const emptyPersonas: AgentPersona[] = [];

      expect(() => {
        render(<AnalyticsCharts metrics={emptyMetrics} agents={emptyPersonas} />);
      }).not.toThrow();

      expect(screen.getByText(/Performance & Benchmark Analytics/i)).toBeInTheDocument();
    });
  });
});
