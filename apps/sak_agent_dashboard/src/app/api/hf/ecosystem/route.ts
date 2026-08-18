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
    const { action, repoId, content, factoryRebuild } = body;

    if (action === "validate_card" && repoId && content) {
      const result = hfEcosystemEngine.validateCard(repoId, content);
      return NextResponse.json({ success: true, result });
    }

    if (action === "diagnose_space" && repoId) {
      const diag = hfEcosystemEngine.diagnoseSpace(repoId);
      return NextResponse.json({ success: true, diagnostic: diag });
    }

    if (action === "remediate_space" && repoId) {
      const outcome = hfEcosystemEngine.remediateSpace(repoId, !!factoryRebuild);
      return NextResponse.json({ success: true, outcome });
    }

    if (action === "preview_all_cards") {
      const previews = hfEcosystemEngine.previewAllCards();
      return NextResponse.json({ success: true, previews });
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
