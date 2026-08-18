import { NextResponse } from "next/server";
import { getMemoryData } from "@/lib/db";
import { getAuditLogs } from "@/lib/sakthai";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const demo = url.searchParams.get("demo") === "true";
    const query = url.searchParams.get("query") || undefined;
    const severity = url.searchParams.get("severity") || undefined;

    const { memory, dataSource } = await getMemoryData(demo, query);
    const { logs: auditLogs, dataSource: auditDataSource } = await getAuditLogs(
      demo,
      severity
    );

    return NextResponse.json({
      success: true,
      memory,
      auditLogs,
      dataSource,
      auditDataSource,
    });
  } catch (error: any) {
    console.error("Secure Log [GET /api/memory]: Failed to fetch memory data:", error);
    return NextResponse.json(
      { success: false, error: "An unexpected error occurred while fetching memory data." },
      { status: 500 }
    );
  }
}
