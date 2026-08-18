import { NextResponse } from "next/server";
import { getChatKitData } from "@/lib/chatkit";

export async function GET() {
  try {
    const chatkit = getChatKitData();
    return NextResponse.json({ success: true, chatkit });
  } catch (error: any) {
    console.error("Secure Log [GET /api/chatkit]: Failed to load ChatKit data:", error);
    return NextResponse.json(
      {
        success: false,
        chatkit: null,
        error: "An unexpected error occurred while loading ChatKit data.",
      },
      { status: 500 }
    );
  }
}
