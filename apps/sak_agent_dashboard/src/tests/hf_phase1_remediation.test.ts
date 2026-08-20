import { describe, it, expect } from "vitest";
import { hfEcosystemEngine } from "@/lib/hfEcosystemEngine";

describe("HF Ecosystem Phase 1 Suite", () => {
  it("diagnoses space runtime status properly", () => {
    const chatDiag = hfEcosystemEngine.diagnoseSpace("sakthai-chat");
    expect(chatDiag.repoId).toBe("sakthai-chat");
    expect(["RUNNING", "SLEEPING", "STOPPED"]).toContain(chatDiag.state);
  });

  it("triggers space remediation actions", () => {
    const outcome = hfEcosystemEngine.remediateSpace("sakthai-tts", false);
    expect(outcome.success).toBe(true);
    expect(outcome.state).toBe("RUNNING");
  });

  it("generates preview audit for all model and dataset cards", () => {
    const previews = hfEcosystemEngine.previewAllCards();
    expect(previews.length).toBeGreaterThanOrEqual(8);
    previews.forEach((p) => {
      expect(p.valid).toBe(true);
      expect(p.score).toBeGreaterThanOrEqual(70);
    });
  });
});
