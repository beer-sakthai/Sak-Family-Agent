import { NextResponse } from "next/server";
import { getMetricsSummary } from "@/lib/sakthai";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const demo = url.searchParams.get("demo") === "true";
    const metrics = await getMetricsSummary(demo);
    return NextResponse.json({ success: true, metrics });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error?.message || "Failed to fetch metrics data" },
      { status: 500 }
    );
  }
}
