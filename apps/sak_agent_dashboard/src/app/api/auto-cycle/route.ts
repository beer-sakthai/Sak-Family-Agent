import { createApiHandler, createMutationHandler } from "@/lib/api/handler";
import { getAutoCycleData } from "@/lib/autoCycle";
import { CycleEngine } from "@/lib/cycle/cycleEngine";

export const GET = createApiHandler("/api/auto-cycle", async () => {
  const autocycle = getAutoCycleData();
  const cycleStates = CycleEngine.getAllPersonaStates();
  return { autocycle, cycleStates };
});

export const POST = createMutationHandler("/api/auto-cycle", async (body) => {
  const { action, persona = "SakThai", task } = body as Record<string, unknown>;

  if (action === "step") {
    const stepResult = await CycleEngine.stepStage(String(persona), task as string | undefined);
    const state = CycleEngine.getPersonaState(String(persona));
    return { stepResult, state };
  }

  if (action === "run_round") {
    const steps = await CycleEngine.runFullCycle(String(persona), task as string | undefined);
    const state = CycleEngine.getPersonaState(String(persona));
    return { steps, state };
  }

  if (action === "reset") {
    const state = CycleEngine.resetCycle(String(persona));
    return { state };
  }

  throw new Error(`Invalid action: ${action}`);
});
