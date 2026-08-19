import { NextResponse } from "next/server";
import { getOtelData } from "@/lib/otel";

export async function GET() {
  try {
    const otel = getOtelData();
    return NextResponse.json({ success: true, otel });
  } catch (error: any) {
    console.error("Secure Log [GET /api/otel]: Failed to load OTel data:", error);
    return NextResponse.json(
      {
        success: false,
        otel: null,
        error: "An unexpected error occurred while loading OpenTelemetry data.",
      },
      { status: 500 }
    );
  }
}
