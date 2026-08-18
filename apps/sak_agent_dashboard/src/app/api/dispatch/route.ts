import { NextRequest, NextResponse } from "next/server";
import { telemetryBus } from "@/lib/telemetryBus";
import { randomUUID } from "crypto";

export const dynamic = "force-dynamic";

const VALID_PERSONAS = [
  "sakthai",
  "sakjules",
  "sakking",
  "saksee",
  "saksit",
  "saktan",
];

const PERSONA_DISPLAY_NAMES: Record<string, string> = {
  sakthai: "SakThai",
  sakjules: "SakJules",
  sakking: "SakKing",
  saksee: "SakSee",
  saksit: "SakSit",
  saktan: "SakTan",
};

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { persona, task, parameters } = body;

    if (!persona || typeof persona !== "string") {
      return NextResponse.json(
        { success: false, error: "Missing or invalid 'persona' field" },
        { status: 400 }
      );
    }

    const normalizedPersona = persona.trim().toLowerCase();
    if (!VALID_PERSONAS.includes(normalizedPersona)) {
      return NextResponse.json(
        {
          success: false,
          error: `Invalid persona '${persona}'. Valid personas: ${VALID_PERSONAS.map(
            (p) => PERSONA_DISPLAY_NAMES[p]
          ).join(", ")}`,
        },
        { status: 400 }
      );
    }

    if (!task || typeof task !== "string" || !task.trim()) {
      return NextResponse.json(
        { success: false, error: "Task description cannot be empty" },
        { status: 400 }
      );
    }

    const displayName = PERSONA_DISPLAY_NAMES[normalizedPersona];
    const dispatchId = `disp_${randomUUID().slice(0, 8)}`;
    const timestamp = new Date().toISOString();

    // 1. Emit agent dispatch start event to telemetry bus
    telemetryBus.emitEvent({
      type: "agent_dispatch",
      persona: displayName,
      sessionId: dispatchId,
      data: {
        task: task.trim(),
        parameters: parameters || {},
        status: "dispatched",
        dispatchedAt: timestamp,
      },
    });

    // 2. Emit synthetic execution step event
    telemetryBus.emitEvent({
      type: "agent_step",
      persona: displayName,
      sessionId: dispatchId,
      data: {
        step: "Initializing context & guardrail verification",
        phase: "planning",
      },
    });

    return NextResponse.json({
      success: true,
      dispatchId,
      persona: displayName,
      task: task.trim(),
      status: "dispatched",
      timestamp,
      message: `Task successfully dispatched to ${displayName}`,
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Invalid dispatch request",
      },
      { status: 500 }
    );
  }
}
