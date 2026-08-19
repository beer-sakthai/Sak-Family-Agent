import { NextRequest, NextResponse } from "next/server";
import { telemetryBus } from "@/lib/telemetryBus";
import { TelemetryEventType } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { type, persona, data, sessionId } = body;

    if (!type || !persona) {
      return NextResponse.json(
        { success: false, error: "Missing required fields 'type' or 'persona'" },
        { status: 400 }
      );
    }

    const emitted = telemetryBus.emitEvent({
      type: type as TelemetryEventType,
      persona: String(persona),
      sessionId: sessionId ? String(sessionId) : undefined,
      data: data || {},
    });

    return NextResponse.json({ success: true, event: emitted });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "Invalid payload" },
      { status: 400 }
    );
  }
}
