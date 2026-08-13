import { NextResponse } from "next/server";
import { getGenkitData } from "@/lib/genkit";

export async function GET() {
  try {
    const genkit = getGenkitData();
    return NextResponse.json({ success: true, genkit });
  } catch (error: any) {
    console.error("Secure Log [GET /api/genkit]: Failed to load Genkit data:", error);
    return NextResponse.json(
      {
        success: false,
        genkit: null,
        error: "An unexpected error occurred while loading Genkit data.",
      },
      { status: 500 }
    );
  }
}
