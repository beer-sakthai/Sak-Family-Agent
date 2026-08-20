import { NextResponse } from "next/server";
import { getAgentOverview } from "@/lib/sakthai";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const demo = url.searchParams.get("demo") === "true";
    const agents = await getAgentOverview(demo);
    return NextResponse.json({ success: true, agents });
  } catch (error: any) {
    console.error("Secure Log [GET /api/agents]: Failed to fetch agents:", error);
    return NextResponse.json(
      { success: false, error: "An unexpected error occurred while fetching agents data." },
      { status: 500 }
    );
  }
}
