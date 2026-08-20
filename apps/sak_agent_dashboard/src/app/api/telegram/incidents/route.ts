import { ApiError, createApiHandler, createMutationHandler } from "@/lib/api/handler";
import {
  createIncidentAlert,
  getIncidentAlerts,
  PERSONA_VOICES,
  resolveIncidentAlert,
  synthesizePersonaAudio,
} from "@/lib/telegram/voice_bridge";
import { MobileIncidentAlert } from "@/lib/types";

export const dynamic = "force-dynamic";

export const GET = createApiHandler("/api/telegram/incidents", async () => ({
  incidents: getIncidentAlerts(),
  voices: Object.values(PERSONA_VOICES),
}));

export const POST = createMutationHandler("/api/telegram/incidents", async (body) => {
  const action = String(body.action ?? "preview_tts");

  if (action === "preview_tts") {
    return synthesizePersonaAudio(
      String(body.personaSlug ?? "sakthai"),
      String(body.text ?? "ทดสอบระบบเสียงสังเคราะห์ของ Sak-Family"),
    );
  }

  if (action === "create_incident") {
    const alert = createIncidentAlert((body.alert as Partial<MobileIncidentAlert>) ?? {});
    return { alert };
  }

  if (action === "resolve_incident") {
    const status = body.status === "acknowledged" ? "acknowledged" : "resolved";
    const updated = resolveIncidentAlert(String(body.alertId ?? ""), status);
    return { alert: updated };
  }

  throw new ApiError(400, `Unknown action: ${action}`);
});
