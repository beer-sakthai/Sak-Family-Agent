import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { BillingManagementPanel } from "../components/BillingManagementPanel";
import { BillingEngine } from "../lib/billingEngine";

describe("BillingManagementPanel & Engine Suite", () => {
  it("computes and manages quotas correctly in BillingEngine", () => {
    const engine = new BillingEngine();
    const quota = engine.getQuota();
    expect(quota.monthlyTokenQuota).toBeGreaterThan(0);
    expect(quota.remainingTokens).toBeGreaterThan(0);

    const { rawKey, keyItem } = engine.createKey("Test Unit Key");
    expect(rawKey).toContain("sak_live_");
    expect(keyItem.name).toBe("Test Unit Key");

    const revoked = engine.revokeKey(keyItem.keyId);
    expect(revoked).toBe(true);

    const updatedQuota = engine.updateTier("enterprise");
    expect(updatedQuota.tier).toBe("enterprise");
    expect(updatedQuota.monthlyTokenQuota).toBe(100_000_000);
  });

  it("renders billing panel headers and metric labels", () => {
    render(<BillingManagementPanel />);
    expect(screen.getByText(/Token Metering & API Key Billing/i)).toBeDefined();
    expect(screen.getByText(/Monthly Quota/i)).toBeDefined();
    expect(screen.getByText(/Consumed Tokens/i)).toBeDefined();
    expect(screen.getByText(/Remaining Tokens/i)).toBeDefined();
  });
});
