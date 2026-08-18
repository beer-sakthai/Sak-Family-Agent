import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { GET as chatkitGet } from "../app/api/chatkit/route";
import { getChatKitData } from "../lib/chatkit";
import ChatKitPanel from "../components/ChatKitPanel";

describe("ChatKit Feature Suite", () => {
  describe("getChatKitData + /api/chatkit", () => {
    it("returns 4 samples with unique ports and non-empty capabilities", async () => {
      const data = getChatKitData();
      expect(data.samples.length).toBe(4);
      const ports = data.samples.map((s) => s.port);
      expect(new Set(ports).size).toBe(4);
      for (const s of data.samples) {
        expect(s.capabilities.length).toBeGreaterThan(0);
        expect(s.runCommandFromRoot).toMatch(/^npm run /);
        expect(s.runCommandStandalone).toContain("npm install");
      }
      const ids = data.samples.map((s) => s.id);
      expect(ids).toEqual(
        expect.arrayContaining([
          "cat-lounge",
          "customer-support",
          "news-guide",
          "metro-map",
        ])
      );

      const res = await chatkitGet();
      expect(res.status).toBe(200);
      const json = await res.json();
      expect(json.success).toBe(true);
      expect(json.chatkit.samples.length).toBe(4);
    });

    it("names the OPENAI_API_KEY prerequisite", () => {
      const data = getChatKitData();
      const oa = data.prerequisites.find((p) => p.envVar === "OPENAI_API_KEY");
      expect(oa).toBeDefined();
    });

    it("labels every capability that appears in at least one sample", () => {
      const data = getChatKitData();
      const used = new Set<string>();
      for (const s of data.samples) s.capabilities.forEach((c) => used.add(c));
      for (const c of used) {
        expect(data.capabilityLabels[c as keyof typeof data.capabilityLabels]).toBeDefined();
      }
    });
  });

  describe("<ChatKitPanel /> component", () => {
    it("renders header, all 4 samples, and the capability matrix", () => {
      const data = getChatKitData();
      render(<ChatKitPanel data={data} />);
      expect(screen.getByText(/OpenAI ChatKit — Advanced Samples/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Cat Lounge/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Customer Support/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/News Guide/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Metro Map/i).length).toBeGreaterThan(0);
      // Port badge in the header
      expect(screen.getAllByText(/:5170/).length).toBeGreaterThan(0);
      // Capability matrix header
      expect(screen.getByText(/Capability matrix/i)).toBeInTheDocument();
    });

    it("switches a sample's run command between root and standalone modes", () => {
      const data = getChatKitData();
      render(<ChatKitPanel data={data} />);
      // Root command visible by default
      expect(screen.getAllByText(/npm run cat-lounge/i).length).toBeGreaterThan(0);
      // Toggle the first sample to standalone
      const standaloneButtons = screen.getAllByText(/standalone/i);
      fireEvent.click(standaloneButtons[0]);
      expect(
        screen.getByText(/cd cat-lounge && npm install && npm run start/i)
      ).toBeInTheDocument();
    });

    it("renders a loading state when data is null", () => {
      render(<ChatKitPanel data={null} />);
      expect(screen.getByText(/Loading ChatKit sample inventory/i)).toBeInTheDocument();
    });
  });
});
