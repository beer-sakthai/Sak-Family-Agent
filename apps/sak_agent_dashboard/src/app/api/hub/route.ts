import { NextResponse } from "next/server";
import { getHubEcosystemData } from "@/lib/hub";

export async function GET() {
  try {
    const data = getHubEcosystemData();
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
