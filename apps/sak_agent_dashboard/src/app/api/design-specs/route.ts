import { NextResponse } from "next/server";
import { getDesignSpecsData } from "@/lib/designSpecs";

export async function GET() {
  try {
    const specs = getDesignSpecsData();
    return NextResponse.json({ success: true, specs });
  } catch (error: any) {
    console.error("Secure Log [GET /api/design-specs]: Failed to load specs:", error);
    return NextResponse.json(
      {
        success: false,
        specs: { present: false, specsDir: "", plansDir: "", specs: [] },
        error: "An unexpected error occurred while loading design specs.",
      },
      { status: 500 }
    );
  }
}
