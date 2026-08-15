import { NextResponse } from "next/server";
import { getBenchmarkArenaData } from "@/lib/benchmarks";

export async function GET() {
  try {
    const data = getBenchmarkArenaData();
    return NextResponse.json({
      success: true,
      data,
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: (error as Error).message },
      { status: 500 }
    );
  }
}
