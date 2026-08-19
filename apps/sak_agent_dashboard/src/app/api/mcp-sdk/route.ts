import { NextResponse } from "next/server";
import { getMcpSdkData } from "@/lib/mcpSdk";

export async function GET() {
  try {
    const sdk = getMcpSdkData();
    return NextResponse.json({ success: true, sdk });
  } catch (error: any) {
    console.error("Secure Log [GET /api/mcp-sdk]: Failed to load MCP SDK data:", error);
    return NextResponse.json(
      {
        success: false,
        sdk: null,
        error: "An unexpected error occurred while loading MCP SDK data.",
      },
      { status: 500 }
    );
  }
}
