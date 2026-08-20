"use client";

import React, { useState } from "react";
import {
  CreditCard,
  Key,
  ShieldCheck,
  TrendingUp,
  Plus,
  Trash2,
  Copy,
  Check,
  AlertCircle,
  FileText,
  Zap,
} from "lucide-react";
import {
  APIKeyItem,
  InvoiceItem,
  TenantQuotaSummary,
  TenantTier,
  UsageEventItem,
} from "@/lib/billingEngine";
import { usePanelFetch } from "@/lib/hooks/usePanelFetch";

interface BillingApiResponse {
  success: boolean;
  data?: {
    quota: TenantQuotaSummary;
    keys: APIKeyItem[];
    usage: UsageEventItem[];
    invoices: InvoiceItem[];
  };
}

export function BillingManagementPanel() {
  const { data: billingData, refresh } = usePanelFetch<BillingApiResponse>("/api/billing");

  const quota = billingData?.data?.quota ?? null;
  const keys = billingData?.data?.keys ?? [];
  const usage = billingData?.data?.usage ?? [];
  const invoices = billingData?.data?.invoices ?? [];

  const [loading, setLoading] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchBillingData = refresh;

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("/api/billing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "create_key", name: newKeyName }),
      });
      const json = await res.json();
      if (json.success && json.data) {
        setGeneratedKey(json.data.rawKey);
        setNewKeyName("");
        fetchBillingData();
      }
    } catch (err) {
      console.error("Failed to create key", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    try {
      const res = await fetch("/api/billing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "revoke_key", keyId }),
      });
      const json = await res.json();
      if (json.success) {
        fetchBillingData();
      }
    } catch (err) {
      console.error("Failed to revoke key", err);
    }
  };

  const handleTierChange = async (newTier: TenantTier) => {
    try {
      const res = await fetch("/api/billing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "update_tier", tier: newTier }),
      });
      const json = await res.json();
      if (json.success && json.data) {
        fetchBillingData();
      }
    } catch (err) {
      console.error("Failed to update tier", err);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const percentUsed = quota
    ? Math.min(100, Math.round((quota.consumedTokens / quota.monthlyTokenQuota) * 100))
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/60 p-6 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <CreditCard className="w-6 h-6 text-emerald-400" />
            Token Metering & API Key Billing
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Multi-tenant token consumption metering, tier quota management, and cryptographic API keys.
          </p>
        </div>
        <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400">Current Plan:</span>
          <span className="text-xs font-semibold uppercase text-emerald-400 bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-800">
            {quota?.tier || "PRO"}
          </span>
        </div>
      </div>

      {/* Quota Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/50 p-5 rounded-xl border border-slate-800">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs font-medium">Monthly Quota</span>
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {quota?.monthlyTokenQuota.toLocaleString() || "0"}
          </div>
          <div className="text-xs text-slate-500 mt-1">Tokens / month</div>
        </div>

        <div className="bg-slate-900/50 p-5 rounded-xl border border-slate-800">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs font-medium">Consumed Tokens</span>
            <TrendingUp className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-300">
            {quota?.consumedTokens.toLocaleString() || "0"}
          </div>
          <div className="text-xs text-slate-500 mt-1">{percentUsed}% of allocation</div>
        </div>

        <div className="bg-slate-900/50 p-5 rounded-xl border border-slate-800">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs font-medium">Remaining Tokens</span>
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-300">
            {quota?.remainingTokens.toLocaleString() || "0"}
          </div>
          <div className="text-xs text-slate-500 mt-1">Available for inference</div>
        </div>

        <div className="bg-slate-900/50 p-5 rounded-xl border border-slate-800">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs font-medium">Estimated Cost</span>
            <CreditCard className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-300">
            ${quota?.totalCostUsd.toFixed(4) || "0.0000"}
          </div>
          <div className="text-xs text-slate-500 mt-1">Current billing cycle</div>
        </div>
      </div>

      {/* Progress Bar & Tier Selector */}
      <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
        <div className="flex justify-between items-center text-sm">
          <span className="text-slate-300 font-medium">Quota Utilization</span>
          <span className="text-slate-400">{percentUsed}%</span>
        </div>
        <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800">
          <div
            className={`h-full transition-all duration-500 ${
              percentUsed > 90
                ? "bg-red-500"
                : percentUsed > 70
                ? "bg-amber-500"
                : "bg-emerald-500"
            }`}
            style={{ width: `${percentUsed}%` }}
          />
        </div>

        <div className="flex flex-wrap gap-2 pt-2 items-center justify-between">
          <div className="text-xs text-slate-400 flex items-center gap-1.5">
            <AlertCircle className="w-4 h-4 text-slate-500" />
            Quota resets on: {quota ? new Date(quota.resetDate).toLocaleDateString() : "--"}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Switch Tier:</span>
            {(["free", "pro", "enterprise", "pay_as_you_go"] as TenantTier[]).map((t) => (
              <button
                key={t}
                onClick={() => handleTierChange(t)}
                className={`text-xs px-2.5 py-1 rounded transition-colors uppercase font-medium ${
                  quota?.tier === t
                    ? "bg-emerald-500 text-black"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                {t.replace(/_/g, " ")}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* API Key Generator & List */}
      <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Key className="w-5 h-5 text-amber-400" />
            API Keys Management
          </h3>
          <form onSubmit={handleCreateKey} className="flex gap-2 w-full sm:w-auto">
            <input
              type="text"
              placeholder="Key Name (e.g. Prod Bot)"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-white text-xs px-3 py-2 rounded-lg focus:outline-none focus:border-emerald-500 w-full sm:w-60"
            />
            <button
              type="submit"
              disabled={loading || !newKeyName.trim()}
              className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
              Generate Key
            </button>
          </form>
        </div>

        {/* Newly Generated Secret Banner */}
        {generatedKey && (
          <div className="p-4 bg-emerald-950/40 border border-emerald-800/80 rounded-xl space-y-2">
            <div className="flex justify-between items-center text-xs text-emerald-300 font-medium">
              <span>⚠️ Copy your API key now. You will not be able to see it again!</span>
              <button
                onClick={() => setGeneratedKey(null)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <div className="flex items-center gap-2 bg-slate-950 p-2.5 rounded-lg border border-emerald-900">
              <code className="text-xs text-emerald-400 font-mono flex-1 overflow-x-auto">
                {generatedKey}
              </code>
              <button
                onClick={() => copyToClipboard(generatedKey)}
                className="text-xs text-slate-300 hover:text-white bg-slate-800 px-3 py-1.5 rounded flex items-center gap-1"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
          </div>
        )}

        {/* Keys Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider">
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4">Key Token</th>
                <th className="py-3 px-4">Rate Limit</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Created</th>
                <th className="py-3 px-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {keys.map((k) => (
                <tr key={k.keyId} className="hover:bg-slate-800/20 text-slate-300">
                  <td className="py-3 px-4 font-medium text-white">{k.name}</td>
                  <td className="py-3 px-4 font-mono text-slate-400">{k.prefix}</td>
                  <td className="py-3 px-4">{k.rateLimitRpm} req/min</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                        k.isActive
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : "bg-red-950 text-red-400 border border-red-800"
                      }`}
                    >
                      {k.isActive ? "Active" : "Revoked"}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-500">
                    {new Date(k.createdAt).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    {k.isActive && (
                      <button
                        onClick={() => handleRevokeKey(k.keyId)}
                        className="text-red-400 hover:text-red-300 flex items-center gap-1 transition-colors"
                        title="Revoke API Key"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Usage & Invoices Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Usage Events */}
        <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            Recent Usage Events
          </h3>
          <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
            {usage.map((u) => (
              <div
                key={u.eventId}
                className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg flex justify-between items-center text-xs"
              >
                <div>
                  <div className="font-medium text-slate-200">{u.model}</div>
                  <div className="text-[11px] text-slate-500">
                    Prompt: {u.promptTokens} · Compl: {u.completionTokens}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-emerald-400">
                    +{u.totalTokens.toLocaleString()} tok
                  </div>
                  <div className="text-[10px] text-slate-500">${u.costUsd.toFixed(5)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Invoices */}
        <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            Monthly Invoices & Statements
          </h3>
          <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
            {invoices.map((inv) => (
              <div
                key={inv.invoiceId}
                className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg flex justify-between items-center text-xs"
              >
                <div>
                  <div className="font-medium text-slate-200">{inv.invoiceId}</div>
                  <div className="text-[11px] text-slate-500">
                    {new Date(inv.periodStart).toLocaleDateString()} – {new Date(inv.periodEnd).toLocaleDateString()}
                  </div>
                </div>
                <div className="text-right flex items-center gap-3">
                  <div>
                    <div className="font-semibold text-white">${inv.amountDueUsd.toFixed(2)}</div>
                    <div className="text-[10px] text-slate-500">
                      {inv.totalTokens.toLocaleString()} tokens
                    </div>
                  </div>
                  <span className="bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded text-[10px] uppercase font-bold">
                    {inv.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
