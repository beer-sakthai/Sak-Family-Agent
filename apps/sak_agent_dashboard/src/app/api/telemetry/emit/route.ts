import { createMutationHandler, ApiError } from "@/lib/api/handler";
import { telemetryBus } from "@/lib/telemetryBus";
import { TelemetryEventType } from "@/lib/types";

export const dynamic = "force-dynamic";

export const POST = createMutationHandler("/api/telemetry/emit", async (body) => {
  const { type, persona, data, sessionId } = body as Record<string, unknown>;

  if (!type || !persona) {
    throw new ApiError(400, "Missing required fields 'type' or 'persona'");
  }

  const emitted = telemetryBus.emitEvent({
    type: type as TelemetryEventType,
    persona: String(persona),
    sessionId: sessionId ? String(sessionId) : undefined,
    data: (data as Record<string, unknown>) ?? {},
  });

  return { event: emitted };
});
