import { ApiError, createApiHandler, createMutationHandler } from "@/lib/api/handler";
import { selfHealingDashboardEngine } from "@/lib/selfHealingEngine";

export const dynamic = "force-dynamic";

export const GET = createApiHandler("/api/recovery", async () => ({
  data: {
    incidents: selfHealingDashboardEngine.getIncidents(),
    health: selfHealingDashboardEngine.getPersonaHealth(),
    timestamp: new Date().toISOString(),
  },
}));

export const POST = createMutationHandler("/api/recovery", async (body) => {
  const { action, id, persona } = body as Record<string, string>;

  if (action === "replay" && id) {
    const res = selfHealingDashboardEngine.replayIncident(id);
    return { success: res.success, incident: res.incident };
  }

  if (action === "reset_circuit" && persona) {
    return { success: selfHealingDashboardEngine.resetCircuit(persona) };
  }

  throw new ApiError(400, "Invalid recovery action or missing arguments");
});
