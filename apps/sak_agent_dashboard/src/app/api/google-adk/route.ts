import { NextResponse } from "next/server";
import { getAdkData } from "@/lib/googleAdk";

export async function GET() {
  try {
    const adk = getAdkData();
    return NextResponse.json({ success: true, adk });
  } catch (error: any) {
    console.error("Secure Log [GET /api/google-adk]: Failed to load ADK data:", error);
    return NextResponse.json(
      {
        success: false,
        adk: null,
        error: "An unexpected error occurred while loading Google ADK data.",
      },
      { status: 500 }
    );
  }
}
