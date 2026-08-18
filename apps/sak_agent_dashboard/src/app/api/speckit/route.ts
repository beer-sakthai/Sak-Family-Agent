import { NextResponse } from "next/server";
import { getSpecKitData, UPSTREAM } from "@/lib/speckit";

export async function GET() {
  try {
    const speckit = getSpecKitData();
    return NextResponse.json({ success: true, speckit });
  } catch (error: any) {
    console.error("Secure Log [GET /api/speckit]: Failed to load SpecKit data:", error);
    return NextResponse.json(
      {
        success: false,
        speckit: {
          present: false,
          rootPath: "",
          workflows: [],
          integrations: [],
          templates: [],
          scripts: [],
          upstream: UPSTREAM,
        },
        error: "An unexpected error occurred while loading SpecKit data.",
      },
      { status: 500 }
    );
  }
}
