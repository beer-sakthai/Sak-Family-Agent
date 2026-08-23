import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import { POST as dispatchHandler } from "@/app/api/dispatch/route";
import { NextRequest } from "next/server";
import { telemetryBus } from "@/lib/telemetryBus";
import { AgentCard } from "@/components/AgentCard";
import { AgentPersona } from "@/lib/types";

const mockAgent: AgentPersona = {
  name: "SakJules",
  role: "Automation & CI/CD Master",
  status: "Active",
  model: "Gemini 2.5 Pro",
  latencyMs: 142,
  runs: 850,
  skills: ["ci-cd", "selfheal", "test-gen"],
  benchmarkScore: 94.8,
};

describe("Agent Dispatch System", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("API: POST /api/dispatch", () => {
    it("successfully dispatches a task to a valid persona and emits telemetry", async () => {
      const emitSpy = vi.spyOn(telemetryBus, "emitEvent");

      const req = new NextRequest("http://localhost:3000/api/dispatch", {
        method: "POST",
        body: JSON.stringify({
          persona: "SakJules",
          task: "Run comprehensive CI pipeline validation",
        }),
      });

      const res = await dispatchHandler(req);
      expect(res.status).toBe(200);

      const json = await res.json();
      expect(json.success).toBe(true);
      expect(json.persona).toBe("SakJules");
      expect(json.status).toBe("dispatched");
      expect(json.dispatchId).toMatch(/^disp_/);
      expect(json.message).toContain("Task successfully dispatched to SakJules");

      expect(emitSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "agent_dispatch",
          persona: "SakJules",
        })
      );
    });

    it("rejects request with invalid persona", async () => {
      const req = new NextRequest("http://localhost:3000/api/dispatch", {
        method: "POST",
        body: JSON.stringify({
          persona: "InvalidPersonaName",
          task: "Some task",
        }),
      });

      const res = await dispatchHandler(req);
      expect(res.status).toBe(400);

      const json = await res.json();
      expect(json.success).toBe(false);
      expect(json.error).toContain("Invalid persona");
    });



    it("rejects request with non-string persona", async () => {
      const req = new NextRequest("http://localhost:3000/api/dispatch", {
        method: "POST",
        body: JSON.stringify({
          persona: 12345,
          task: "Some task",
        }),
      });

      const res = await dispatchHandler(req);
      expect(res.status).toBe(400);

      const json = await res.json();
      expect(json.success).toBe(false);
      expect(json.error).toContain("Missing or invalid 'persona' field");
    });

    it("rejects request with missing persona", async () => {
      const req = new NextRequest("http://localhost:3000/api/dispatch", {
        method: "POST",
        body: JSON.stringify({
          task: "Some task",
        }),
      });

      const res = await dispatchHandler(req);
      expect(res.status).toBe(400);

      const json = await res.json();
      expect(json.success).toBe(false);
      expect(json.error).toContain("Missing or invalid 'persona' field");
    });

    it("rejects request with empty task", async () => {
      const req = new NextRequest("http://localhost:3000/api/dispatch", {
        method: "POST",
        body: JSON.stringify({
          persona: "SakThai",
          task: "   ",
        }),
      });

      const res = await dispatchHandler(req);
      expect(res.status).toBe(400);

      const json = await res.json();
      expect(json.success).toBe(false);
      expect(json.error).toContain("Task description cannot be empty");
    });
  });

  describe("UI Component: AgentCard Dispatch Console", () => {
    it("renders Dispatch button and opens interactive console when clicked", async () => {
      render(<AgentCard agent={mockAgent} />);

      const dispatchBtn = screen.getByRole("button", {
        name: /Dispatch SakJules/i,
      });
      expect(dispatchBtn).toBeInTheDocument();

      fireEvent.click(dispatchBtn);

      expect(screen.getByText("Live Task Dispatch")).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText("Instruct SakJules...")
      ).toBeInTheDocument();
    });

    it("populates prompt input when clicking a preset button", async () => {
      render(<AgentCard agent={mockAgent} />);

      fireEvent.click(
        screen.getByRole("button", { name: /Dispatch SakJules/i })
      );

      const presetBtn = screen.getByText(
        "Run automated CI/CD gate and test battery"
      );
      fireEvent.click(presetBtn);

      const textarea = screen.getByPlaceholderText(
        "Instruct SakJules..."
      ) as HTMLTextAreaElement;
      expect(textarea.value).toBe("Run automated CI/CD gate and test battery");
    });

    it("submits dispatch form and displays receipt ID", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          dispatchId: "disp_test123",
          message: "Task successfully dispatched to SakJules",
        }),
      });

      render(<AgentCard agent={mockAgent} />);

      fireEvent.click(
        screen.getByRole("button", { name: /Dispatch SakJules/i })
      );

      const textarea = screen.getByPlaceholderText("Instruct SakJules...");
      fireEvent.change(textarea, {
        target: { value: "Verify security guardrails" },
      });

      const submitBtn = screen.getByRole("button", {
        name: /Submit task dispatch/i,
      });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText("Task successfully dispatched to SakJules")
        ).toBeInTheDocument();
        expect(screen.getByText(/Receipt ID: disp_test123/i)).toBeInTheDocument();
      });
    });
  });
});
