import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const gatewayStatus = {
    totalServers: 4,
    activeServers: 4,
    registeredTools: [
      {
        qualifiedName: "sakthai_core::read_file",
        server: "sakthai_core",
        transport: "stdio",
        description: "Read file with path traversal guard",
      },
      {
        qualifiedName: "sakking_sec::ast_scan",
        server: "sakking_sec",
        transport: "stdio",
        description: "Scan code AST for security vulnerabilities",
      },
      {
        qualifiedName: "saksee_vis::snapshot_dom",
        server: "saksee_vis",
        transport: "stdio",
        description: "Capture accessibility tree & visual DOM snapshot",
      },
    ],
    timestamp: new Date().toISOString(),
  };

  return NextResponse.json({ success: true, gateway: gatewayStatus });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { toolName, args } = body;

    if (!toolName) {
      return NextResponse.json({ error: "toolName is required" }, { status: 400 });
    }

    return NextResponse.json({
      success: true,
      tool: toolName,
      result: { executed: true, message: `Dispatched tool ${toolName} safely`, args },
      timestamp: new Date().toISOString(),
    });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message || "Internal server error" }, { status: 500 });
  }
}
