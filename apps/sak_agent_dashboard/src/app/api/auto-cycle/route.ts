import { NextRequest, NextResponse } from "next/server";
import { getAutoCycleData } from "@/lib/autoCycle";
import { CycleEngine } from "@/lib/cycle/cycleEngine";

export async function GET() {
  try {
    const autocycle = getAutoCycleData();
    const cycleStates = CycleEngine.getAllPersonaStates();

    return NextResponse.json({
      success: true,
      autocycle,
      cycleStates,
    });
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : "Failed to load auto-cycle data";
    console.error("Secure Log [GET /api/auto-cycle]:", error);
    return NextResponse.json(
      { success: false, autocycle: null, error: msg },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, persona = "SakThai", task } = body;

    if (action === "step") {
      const stepResult = await CycleEngine.stepStage(persona, task);
      const state = CycleEngine.getPersonaState(persona);
      return NextResponse.json({ success: true, stepResult, state });
    }

    if (action === "run_round") {
      const steps = await CycleEngine.runFullCycle(persona, task);
      const state = CycleEngine.getPersonaState(persona);
      return NextResponse.json({ success: true, steps, state });
    }

    if (action === "reset") {
      const state = CycleEngine.resetCycle(persona);
      return NextResponse.json({ success: true, state });
    }

    return NextResponse.json(
      { success: false, error: `Invalid action: ${action}` },
      { status: 400 }
    );
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : "Cycle execution error";
    console.error("Secure Log [POST /api/auto-cycle]:", error);
    return NextResponse.json({ success: false, error: msg }, { status: 500 });
  }
}
