import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { AgentCard } from "../components/AgentCard";
import { AgentOverview } from "../components/AgentOverview";
import { AnalyticsCharts } from "../components/AnalyticsCharts";
import { SessionExplorer } from "../components/SessionExplorer";
import { MemoryExplorer } from "../components/MemoryExplorer";
import { AuditLogs } from "../components/AuditLogs";
import { DemoModeToggle } from "../components/DemoModeToggle";
import { StitchStudio } from "../components/StitchStudio";
import { LiveTelemetryFeed } from "../components/LiveTelemetryFeed";

describe("UI Components Test Suite (Tier 1 & Tier 2)", () => {

  describe("AgentCard & AgentOverview Components", () => {
    it("renders agent card details when AgentCard is invoked", () => {
      const sampleAgent = {
        name: "SakThai",
        role: "Primary Orchestrator & Fine-Tuned Agent",
        status: "Active" as const,
        model: "sakthai-v2-qlora",
        latencyMs: 320,
        runs: 300,
        skills: ["routing", "planning", "tool-call"],
      };

      render(<AgentCard agent={sampleAgent} />);
      expect(screen.getByText("SakThai")).toBeInTheDocument();
      expect(screen.getByText("Primary Orchestrator & Fine-Tuned Agent")).toBeInTheDocument();
      expect(screen.getByText("Active")).toBeInTheDocument();
      expect(screen.getByText(/320ms/)).toBeInTheDocument();
    });

    it("renders overview grid with all 5 Sak-Agent-Family personas", () => {
      const mockAgents = [
        { name: "SakThai", role: "Primary Orchestrator", status: "Active" as const, model: "m1", latencyMs: 300, runs: 100, skills: [] },
        { name: "SakKing", role: "Reasoning Specialist", status: "Ready" as const, model: "m2", latencyMs: 500, runs: 80, skills: [] },
        { name: "SakSee", role: "Multimodal Specialist", status: "Ready" as const, model: "m3", latencyMs: 400, runs: 60, skills: [] },
        { name: "SakSit", role: "Security Auditor", status: "Ready" as const, model: "m4", latencyMs: 280, runs: 50, skills: [] },
        { name: "SakJules", role: "Async Execution", status: "Ready" as const, model: "m5", latencyMs: 350, runs: 70, skills: [] },
      ];

      render(<AgentOverview agents={mockAgents} />);
      expect(screen.getByText("SakThai")).toBeInTheDocument();
      expect(screen.getByText("SakKing")).toBeInTheDocument();
      expect(screen.getByText("SakSee")).toBeInTheDocument();
      expect(screen.getByText("SakSit")).toBeInTheDocument();
      expect(screen.getByText("SakJules")).toBeInTheDocument();
    });
  });

  describe("AnalyticsCharts Component", () => {
    it("renders token usage and benchmark analytics sections", () => {
      const mockMetrics = {
        totalRuns: 761,
        avgLatencyMs: 388,
        successRate: 0.985,
        tokenStats: { totalTokens: 1450000, promptTokens: 950000, completionTokens: 500000 },
        stopReasons: { end_turn: 740, max_tokens: 21 },
        trends: [{ date: "2026-08-01", runs: 350, latencyMs: 380 }],
      };

      render(<AnalyticsCharts metrics={mockMetrics} />);
      expect(screen.getByText(/Token Usage/i)).toBeInTheDocument();
    });
  });

  describe("SessionExplorer Component", () => {
    it("allows interactive search query input and renders session rows", () => {
      const mockSessions = [
        { sessionId: "sess-1", persona: "SakThai", timestamp: "2026-08-02", messageCount: 5, tokenUsage: 1200, status: "completed" as const },
        { sessionId: "sess-2", persona: "SakKing", timestamp: "2026-08-02", messageCount: 10, tokenUsage: 3400, status: "completed" as const },
      ];

      render(<SessionExplorer sessions={mockSessions} />);
      const searchInput = screen.getByPlaceholderText(/search/i);
      fireEvent.change(searchInput, { target: { value: "SakThai" } });
      expect(searchInput).toHaveValue("SakThai");
    });
  });

  describe("MemoryExplorer & AuditLogs Components", () => {
    it("renders MemoryExplorer with facts and observations", () => {
      const mockMemory = {
        facts: [{ id: 1, entity: "SakThai", fact: "Primary model initialized", persona: "SakThai" }],
        observations: [{ id: 1, category: "eval", observation: "Benchmark 95% passed" }],
      };

      render(<MemoryExplorer memory={mockMemory} />);
      expect(screen.getByText("Primary model initialized")).toBeInTheDocument();
    });

    it("renders security audit log entries with severity badges", () => {
      const mockLogs = [
        { id: 1, timestamp: "2026-08-02T12:00:00Z", persona: "SakSit", severity: "critical" as const, event: "Unauthorized access blocked", details: "Blocked IP 10.0.0.1" },
        { id: 2, timestamp: "2026-08-02T12:05:00Z", persona: "SakThai", severity: "info" as const, event: "Session initialized", details: "OK" },
      ];

      render(<AuditLogs logs={mockLogs} />);
      expect(screen.getByText("Unauthorized access blocked")).toBeInTheDocument();
      expect(screen.getByText("critical")).toBeInTheDocument();
    });
  });

  describe("Demo Mode Toggle Component", () => {
    it("renders demo mode toggle button with aria-pressed state and handles click state toggle", () => {
      const handleToggle = vi.fn();

      render(<DemoModeToggle isDemo={false} onToggle={handleToggle} />);
      const btn = screen.getByRole("button", { name: /demo mode/i });
      expect(btn.getAttribute("aria-pressed")).toBe("false");
      fireEvent.click(btn);
      expect(handleToggle).toHaveBeenCalled();
    });
  });

  describe("StitchStudio Component", () => {
    it("renders Stitch Studio header, preset controls, and tab switching", () => {
      render(<StitchStudio />);
      expect(screen.getByText(/Google Stitch Design & Component Workbench/i)).toBeInTheDocument();
      expect(screen.getByText(/SakThai Interactive Agent Drawer/i)).toBeInTheDocument();
      const codeTab = screen.getByRole("button", { name: /tsx code/i });
      fireEvent.click(codeTab);
      expect(screen.getByText(/SakThaiAgentCard/i)).toBeInTheDocument();
    });
  });
  describe("LiveTelemetryFeed Component Accessibility", () => {
    it("renders control buttons and select input with appropriate ARIA labels", () => {
      render(<LiveTelemetryFeed />);
      const clearBtn = screen.getByRole("button", { name: "Clear Stream" });
      expect(clearBtn).toBeInTheDocument();
      expect(clearBtn).toBeDisabled();
      expect(clearBtn).toHaveAttribute("title", "Stream is empty");
      expect(screen.getByRole("button", { name: "Pause stream" })).toBeInTheDocument();
      expect(screen.getByRole("combobox", { name: "Filter by Persona" })).toBeInTheDocument();
    });
  });
});
