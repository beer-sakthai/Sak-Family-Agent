export type TenantTier = "free" | "pro" | "enterprise" | "pay_as_you_go";

export interface APIKeyItem {
  keyId: string;
  name: string;
  prefix: string;
  tier: TenantTier;
  isActive: boolean;
  createdAt: string;
  lastUsedAt?: string | null;
  rateLimitRpm: number;
}

export interface TenantQuotaSummary {
  tenantId: string;
  tier: TenantTier;
  monthlyTokenQuota: number;
  consumedTokens: number;
  remainingTokens: number;
  totalCostUsd: number;
  activeKeysCount: number;
  resetDate: string;
}

export interface UsageEventItem {
  eventId: string;
  model: string;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  costUsd: number;
  timestamp: string;
}

export interface InvoiceItem {
  invoiceId: string;
  periodStart: string;
  periodEnd: string;
  totalRequests: number;
  totalTokens: number;
  amountDueUsd: number;
  status: "paid" | "due" | "waived";
}

export class BillingEngine {
  private quota: TenantQuotaSummary = {
    tenantId: "tenant_default",
    tier: "pro",
    monthlyTokenQuota: 5_000_000,
    consumedTokens: 1_284_950,
    remainingTokens: 3_715_050,
    totalCostUsd: 1.84,
    activeKeysCount: 3,
    resetDate: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1).toISOString(),
  };

  private keys: APIKeyItem[] = [
    {
      keyId: "key_prod_bot_01",
      name: "Production Telegram Bot",
      prefix: "sak_live_9a7f...",
      tier: "pro",
      isActive: true,
      createdAt: "2026-08-01T10:00:00Z",
      lastUsedAt: "2026-08-18T15:20:00Z",
      rateLimitRpm: 300,
    },
    {
      keyId: "key_dev_testing_02",
      name: "Staging / Local Dev",
      prefix: "sak_live_4b2c...",
      tier: "pro",
      isActive: true,
      createdAt: "2026-08-10T14:30:00Z",
      lastUsedAt: "2026-08-18T14:45:00Z",
      rateLimitRpm: 300,
    },
  ];

  private usage: UsageEventItem[] = [
    {
      eventId: "evt_9918",
      model: "sakthai-context-1.5b-merged",
      promptTokens: 4200,
      completionTokens: 850,
      totalTokens: 5050,
      costUsd: 0.00114,
      timestamp: "2026-08-18T15:20:10Z",
    },
    {
      eventId: "evt_9917",
      model: "sakthai-coder-1.5b",
      promptTokens: 8100,
      completionTokens: 1200,
      totalTokens: 9300,
      costUsd: 0.001935,
      timestamp: "2026-08-18T15:15:00Z",
    },
    {
      eventId: "evt_9916",
      model: "sakthai-vision-7b",
      promptTokens: 12400,
      completionTokens: 2100,
      totalTokens: 14500,
      costUsd: 0.00312,
      timestamp: "2026-08-18T15:02:40Z",
    },
  ];

  private invoices: InvoiceItem[] = [
    {
      invoiceId: "inv_202607_8f91a",
      periodStart: "2026-07-01T00:00:00Z",
      periodEnd: "2026-07-31T23:59:59Z",
      totalRequests: 1420,
      totalTokens: 4_210_000,
      amountDueUsd: 4.85,
      status: "paid",
    },
  ];

  getQuota(): TenantQuotaSummary {
    return { ...this.quota };
  }

  getKeys(): APIKeyItem[] {
    return [...this.keys];
  }

  getUsage(): UsageEventItem[] {
    return [...this.usage];
  }

  getInvoices(): InvoiceItem[] {
    return [...this.invoices];
  }

  createKey(name: string): { rawKey: string; keyItem: APIKeyItem } {
    const randomHex = Math.random().toString(36).substring(2, 10);
    const rawKey = `sak_live_${randomHex}${Date.now().toString(36)}`;
    const keyItem: APIKeyItem = {
      keyId: `key_${Date.now().toString(36)}`,
      name: name.trim() || "Default API Key",
      prefix: rawKey.slice(0, 12) + "...",
      tier: this.quota.tier,
      isActive: true,
      createdAt: new Date().toISOString(),
      rateLimitRpm: 300,
    };
    this.keys.unshift(keyItem);
    this.quota.activeKeysCount = this.keys.filter((k) => k.isActive).length;
    return { rawKey, keyItem };
  }

  revokeKey(keyId: string): boolean {
    const target = this.keys.find((k) => k.keyId === keyId);
    if (!target) return false;
    target.isActive = false;
    this.quota.activeKeysCount = this.keys.filter((k) => k.isActive).length;
    return true;
  }

  updateTier(tier: TenantTier): TenantQuotaSummary {
    this.quota.tier = tier;
    if (tier === "free") this.quota.monthlyTokenQuota = 100_000;
    else if (tier === "pro") this.quota.monthlyTokenQuota = 5_000_000;
    else if (tier === "enterprise") this.quota.monthlyTokenQuota = 100_000_000;
    else this.quota.monthlyTokenQuota = 1_000_000_000;
    this.quota.remainingTokens = Math.max(0, this.quota.monthlyTokenQuota - this.quota.consumedTokens);
    return { ...this.quota };
  }
}

export const billingEngine = new BillingEngine();
