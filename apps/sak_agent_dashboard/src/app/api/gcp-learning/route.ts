import { NextResponse } from "next/server";
import { getGcpLearningData } from "@/lib/gcpLearning";

export async function GET() {
  try {
    const learning = getGcpLearningData();
    return NextResponse.json({ success: true, learning });
  } catch (error: any) {
    console.error("Secure Log [GET /api/gcp-learning]: Failed to load GCP Learning data:", error);
    return NextResponse.json(
      {
        success: false,
        learning: null,
        error: "An unexpected error occurred while loading GCP Learning data.",
      },
      { status: 500 }
    );
  }
}
