import { NextResponse } from "next/server";
import { getSelfEvolutionData } from "@/lib/selfEvolution";

export async function GET() {
  try {
    const data = getSelfEvolutionData();
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
