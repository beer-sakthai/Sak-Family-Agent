import { NextResponse } from "next/server";
import { getSessionTranscripts } from "@/lib/sakthai";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const demo = url.searchParams.get("demo") === "true";
    const search = url.searchParams.get("search") || url.searchParams.get("query") || undefined;
    const id = url.searchParams.get("id") || undefined;

    const rawLimit = url.searchParams.get("limit");
    const rawOffset = url.searchParams.get("offset");

    const limit = rawLimit !== null ? parseInt(rawLimit, 10) : 20;
    const offset = rawOffset !== null ? parseInt(rawOffset, 10) : 0;

    const result = await getSessionTranscripts({
      demo,
      search,
      limit,
      offset,
      id,
    });

    return NextResponse.json({
      success: true,
      sessions: result.sessions,
      total: result.total,
      dataSource: result.dataSource,
      ...(result.detail ? { detail: result.detail } : {}),
    });
  } catch (error: any) {
    console.error("Secure Log [GET /api/sessions]: Failed to fetch sessions data:", error);
    return NextResponse.json(
      { success: false, error: "An unexpected error occurred while fetching sessions data." },
      { status: 500 }
    );
  }
}
