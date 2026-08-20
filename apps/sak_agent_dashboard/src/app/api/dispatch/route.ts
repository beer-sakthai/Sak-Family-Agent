import { createMutationHandler, ApiError } from "@/lib/api/handler";
import { telemetryBus } from "@/lib/telemetryBus";
import { randomUUID } from "crypto";

export const dynamic = "force-dynamic";

const VALID_PERSONAS = ["sakthai", "sakjules", "sakking", "saksee", "saksit", "saktan"];
const PERSONA_DISPLAY_NAMES: Record<string, string> = {
  sakthai: "SakThai",
  sakjules: "SakJules",
  sakking: "SakKing",
  saksee: "SakSee",
  saksit: "SakSit",
  saktan: "SakTan",
};

export const POST = createMutationHandler("/api/dispatch", async (body) => {
  const { persona, task, parameters } = body as Record<string, unknown>;

  if (!persona || typeof persona !== "string") {
    throw new ApiError(400, "Missing or invalid 'persona' field");
  }

  const normalizedPersona = persona.trim().toLowerCase();
  if (!VALID_PERSONAS.includes(normalizedPersona)) {
    throw new ApiError(
      400,
      `Invalid persona '${persona}'. Valid personas: ${VALID_PERSONAS.map((p) => PERSONA_DISPLAY_NAMES[p]).join(", ")}`,
    );
  }

  if (!task || typeof task !== "string" || !task.trim()) {
    throw new ApiError(400, "Task description cannot be empty");
  }

  const displayName = PERSONA_DISPLAY_NAMES[normalizedPersona];
  const dispatchId = `disp_${randomUUID().slice(0, 8)}`;
  const timestamp = new Date().toISOString();

  telemetryBus.emitEvent({
    type: "agent_dispatch",
    persona: displayName,
    sessionId: dispatchId,
    data: {
      task: task.trim(),
      parameters: (parameters as Record<string, unknown>) ?? {},
      status: "dispatched",
      dispatchedAt: timestamp,
    },
  });

  telemetryBus.emitEvent({
    type: "agent_step",
    persona: displayName,
    sessionId: dispatchId,
    data: { step: "Initializing context & guardrail verification", phase: "planning" },
  });

  return {
    dispatchId,
    persona: displayName,
    task: task.trim(),
    status: "dispatched",
    timestamp,
    message: `Task successfully dispatched to ${displayName}`,
  };
});
