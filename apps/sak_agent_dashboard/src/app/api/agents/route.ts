import { NextResponse } from "next/server";
import { getAgentOverview } from "@/lib/sakthai";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const demo = url.searchParams.get("demo") === "true";
    const agents = await getAgentOverview(demo);
    return NextResponse.json({ success: true, agents });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error?.message || "Failed to fetch agents data" },
      { status: 500 }
    );
  }
}
