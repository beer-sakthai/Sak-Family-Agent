import { NextResponse } from "next/server";
import { getConductorData } from "@/lib/conductor";

export async function GET() {
  try {
    const conductor = getConductorData();
    return NextResponse.json({ success: true, conductor });
  } catch (error: any) {
    console.error("Secure Log [GET /api/conductor]: Failed to load Conductor data:", error);
    return NextResponse.json(
      {
        success: false,
        conductor: null,
        error: "An unexpected error occurred while loading Conductor data.",
      },
      { status: 500 }
    );
  }
}
