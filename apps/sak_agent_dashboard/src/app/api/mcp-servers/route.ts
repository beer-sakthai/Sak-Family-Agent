import { NextResponse } from "next/server";
import { getMcpServers } from "@/lib/mcpServers";

export async function GET() {
  try {
    const servers = getMcpServers();
    return NextResponse.json({ success: true, servers });
  } catch (error: any) {
    console.error("Secure Log [GET /api/mcp-servers]: Failed to fetch servers:", error);
    return NextResponse.json(
      {
        success: false,
        servers: [],
        error: "An unexpected error occurred while fetching MCP server inventory.",
      },
      { status: 500 }
    );
  }
}
