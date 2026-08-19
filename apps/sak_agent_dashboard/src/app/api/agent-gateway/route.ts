import { NextResponse } from "next/server";
import { getGatewayData } from "@/lib/agentGateway";

export async function GET() {
  try {
    const gateway = getGatewayData();
    return NextResponse.json({ success: true, gateway });
  } catch (error: any) {
    console.error("Secure Log [GET /api/agent-gateway]: Failed to load gateway data:", error);
    return NextResponse.json(
      {
        success: false,
        gateway: null,
        error: "An unexpected error occurred while loading Agent Gateway data.",
      },
      { status: 500 }
    );
  }
}
