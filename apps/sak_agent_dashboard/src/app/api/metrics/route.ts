import { NextResponse } from "next/server";
import { getMetricsSummary } from "@/lib/sakthai";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const demo = url.searchParams.get("demo") === "true";
    const { metrics, dataSource } = await getMetricsSummary(demo);
    return NextResponse.json({ success: true, metrics, dataSource });
  } catch (error: any) {
    console.error("Secure Log [GET /api/metrics]: Failed to fetch metrics:", error);
    return NextResponse.json(
      { success: false, error: "An unexpected error occurred while fetching metrics data." },
      { status: 500 }
    );
  }
}
