import { NextResponse } from "next/server";
import { getM365CopilotData } from "@/lib/m365Copilot";

export async function GET() {
  try {
    const m365 = getM365CopilotData();
    return NextResponse.json({ success: true, m365 });
  } catch (error: any) {
    console.error("Secure Log [GET /api/m365-copilot]: Failed to load M365 Copilot data:", error);
    return NextResponse.json(
      {
        success: false,
        m365: null,
        error: "An unexpected error occurred while loading M365 Copilot data.",
      },
      { status: 500 }
    );
  }
}
