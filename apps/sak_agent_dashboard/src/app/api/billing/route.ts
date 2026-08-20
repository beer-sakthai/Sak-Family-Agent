import { createApiHandler, createMutationHandler } from "@/lib/api/handler";
import { billingEngine, TenantTier } from "@/lib/billingEngine";

export const GET = createApiHandler("/api/billing", async () => {
  const quota = billingEngine.getQuota();
  const keys = billingEngine.getKeys();
  const usage = billingEngine.getUsage();
  const invoices = billingEngine.getInvoices();
  return { data: { quota, keys, usage, invoices } };
});

export const POST = createMutationHandler("/api/billing", async (body) => {
  const { action } = body as Record<string, string>;

  if (action === "create_key") {
    const result = billingEngine.createKey(String(body.name ?? "New API Key"));
    return { data: result };
  }

  if (action === "revoke_key") {
    const success = billingEngine.revokeKey(String(body.keyId ?? ""));
    return { success, message: success ? "API key revoked" : "API key not found" };
  }

  if (action === "update_tier") {
    const quota = billingEngine.updateTier(body.tier as TenantTier);
    return { data: quota };
  }

  throw new Error(`Unsupported action: ${action}`);
});
