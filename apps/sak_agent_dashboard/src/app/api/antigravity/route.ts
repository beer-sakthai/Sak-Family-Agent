import { NextResponse } from "next/server";
import { getAntigravityData } from "@/lib/antigravity";

export async function GET() {
  try {
    const antigravity = getAntigravityData();
    return NextResponse.json({ success: true, antigravity });
  } catch (error: any) {
    console.error("Secure Log [GET /api/antigravity]: Failed to load Antigravity data:", error);
    return NextResponse.json(
      {
        success: false,
        antigravity: null,
        error: "An unexpected error occurred while loading Antigravity data.",
      },
      { status: 500 }
    );
  }
}
