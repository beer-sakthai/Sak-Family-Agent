import { NextResponse } from "next/server";
import { billingEngine, TenantTier } from "@/lib/billingEngine";

export async function GET() {
  const quota = billingEngine.getQuota();
  const keys = billingEngine.getKeys();
  const usage = billingEngine.getUsage();
  const invoices = billingEngine.getInvoices();

  return NextResponse.json({
    success: true,
    data: {
      quota,
      keys,
      usage,
      invoices,
    },
  });
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { action } = body;

    if (action === "create_key") {
      const { name } = body;
      const result = billingEngine.createKey(name || "New API Key");
      return NextResponse.json({
        success: true,
        data: result,
      });
    }

    if (action === "revoke_key") {
      const { keyId } = body;
      const success = billingEngine.revokeKey(keyId);
      return NextResponse.json({
        success,
        message: success ? "API key revoked" : "API key not found",
      });
    }

    if (action === "update_tier") {
      const { tier } = body as { tier: TenantTier };
      const quota = billingEngine.updateTier(tier);
      return NextResponse.json({
        success: true,
        data: quota,
      });
    }

    return NextResponse.json(
      { success: false, error: `Unsupported action: ${action}` },
      { status: 400 }
    );
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : "Internal Server Error";
    return NextResponse.json(
      { success: false, error: errorMsg },
      { status: 500 }
    );
  }
}
