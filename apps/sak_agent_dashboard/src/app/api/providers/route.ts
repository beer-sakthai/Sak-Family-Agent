import { NextResponse } from "next/server";
import { PROVIDERS } from "@/lib/providers";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return NextResponse.json({
      success: true,
      providers: PROVIDERS,
      totalProviders: PROVIDERS.length,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch providers",
      },
      { status: 500 }
    );
  }
}
