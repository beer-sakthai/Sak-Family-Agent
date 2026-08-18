import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import GatewayRouterPanel from "@/components/GatewayRouterPanel";

describe("GatewayRouterPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders header, active badge, preset buttons, and input form", () => {
    render(<GatewayRouterPanel />);

    expect(screen.getByText(/Multi-Agent Gateway Router & Session Manager/i)).toBeInTheDocument();
    expect(screen.getByText(/Gateway Active/i)).toBeInTheDocument();
    expect(screen.getByText(/CI\/CD Pipeline Fix/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Type query or use @sakjules/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Dispatch Query/i })).toBeInTheDocument();
  });

  it("populates input and triggers route when clicking a preset button", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        selectedPersona: "sakjules",
        roleDeclaration: "**SakJules · Master of Automation & CI/CD.**",
        intent: "automation_ci",
        confidence: 0.98,
        matchedKeywords: ["workflow", "docker"],
        chargeLevel: 100,
        reply: "**SakJules · Master of Automation & CI/CD.**\n\nProcessed query with specialized intent 'automation_ci'.",
      }),
    });
    global.fetch = mockFetch;

    render(<GatewayRouterPanel />);

    const presetBtn = screen.getByText(/CI\/CD Pipeline Fix/i);
    fireEvent.click(presetBtn);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/gateway",
        expect.objectContaining({
          method: "POST",
        })
      );
    });

    await waitFor(() => {
      expect(screen.getAllByText(/sakjules/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("automation_ci")).toBeInTheDocument();
      expect(screen.getByText("98%")).toBeInTheDocument();
    });
  });

  it("submits manual query and displays routing outcome", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        selectedPersona: "saksee",
        roleDeclaration: "**SakSee · Deep Research & Visual Intelligence.**",
        intent: "research",
        confidence: 0.95,
        matchedKeywords: ["arxiv", "paper"],
        chargeLevel: 90,
        reply: "**SakSee · Deep Research & Visual Intelligence.**\n\nProcessed query.",
      }),
    });
    global.fetch = mockFetch;

    render(<GatewayRouterPanel />);

    const input = screen.getByPlaceholderText(/Type query or use @sakjules/i);
    fireEvent.change(input, { target: { value: "Research new papers" } });

    const submitBtn = screen.getByRole("button", { name: /Dispatch Query/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getAllByText(/saksee/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("90%")).toBeInTheDocument();
    });
  });
});
