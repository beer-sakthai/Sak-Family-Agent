import { NextRequest, NextResponse } from "next/server";
import { hfEcosystemEngine } from "@/lib/hfEcosystemEngine";

export const dynamic = "force-dynamic";

export async function GET() {
  const summary = hfEcosystemEngine.getEcosystemSummary();
  return NextResponse.json({
    success: true,
    data: {
      summary,
      timestamp: new Date().toISOString(),
    },
  });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { action, repoId, content } = body;

    if (action === "validate_card" && repoId && content) {
      const result = hfEcosystemEngine.validateCard(repoId, content);
      return NextResponse.json({ success: true, result });
    }

    return NextResponse.json(
      { success: false, error: "Invalid action or missing parameters" },
      { status: 400 }
    );
  } catch (err: any) {
    return NextResponse.json(
      { success: false, error: err?.message || "Internal server error" },
      { status: 500 }
    );
  }
}
