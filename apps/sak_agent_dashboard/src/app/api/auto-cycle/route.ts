import { NextResponse } from "next/server";
import { getAutoCycleData } from "@/lib/autoCycle";

export async function GET() {
  try {
    const autocycle = getAutoCycleData();
    return NextResponse.json({ success: true, autocycle });
  } catch (error: any) {
    console.error("Secure Log [GET /api/auto-cycle]: Failed to load auto-cycle data:", error);
    return NextResponse.json(
      {
        success: false,
        autocycle: null,
        error: "An unexpected error occurred while loading auto-cycle data.",
      },
      { status: 500 }
    );
  }
}
