import { NextRequest, NextResponse } from "next/server";
import { selfHealingDashboardEngine } from "@/lib/selfHealingEngine";

export const dynamic = "force-dynamic";

export async function GET() {
  const incidents = selfHealingDashboardEngine.getIncidents();
  const health = selfHealingDashboardEngine.getPersonaHealth();
  return NextResponse.json({
    success: true,
    data: {
      incidents,
      health,
      timestamp: new Date().toISOString(),
    },
  });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { action, id, persona } = body;

    if (action === "replay" && id) {
      const res = selfHealingDashboardEngine.replayIncident(id);
      return NextResponse.json({ success: res.success, incident: res.incident });
    }

    if (action === "reset_circuit" && persona) {
      const res = selfHealingDashboardEngine.resetCircuit(persona);
      return NextResponse.json({ success: res });
    }

    return NextResponse.json(
      { success: false, error: "Invalid recovery action or missing arguments" },
      { status: 400 }
    );
  } catch (err: any) {
    return NextResponse.json(
      { success: false, error: err?.message || "Internal server error" },
      { status: 500 }
    );
  }
}
