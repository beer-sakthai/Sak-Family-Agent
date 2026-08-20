import { createApiHandler, createMutationHandler } from "@/lib/api/handler";
import { RedTeamEngine } from "@/lib/redteam/redTeamEngine";
import { AttackVector, FuzzingPayload } from "@/lib/redteam/types";

export const GET = createApiHandler("/api/redteam", async (ctx) => {
  const action = ctx.params["action"] ?? "all";

  if (action === "sweeps") return { sweeps: RedTeamEngine.getRecentSweeps() };
  if (action === "verdicts") return { verdicts: RedTeamEngine.getVerdicts() };

  return {
    data: {
      sweeps: RedTeamEngine.getRecentSweeps(),
      payloads: RedTeamEngine.getPayloads(),
      verdicts: RedTeamEngine.getVerdicts(),
    },
  };
});

export const POST = createMutationHandler("/api/redteam", async (body) => {
  const { action } = body as Record<string, unknown>;

  if (action === "fuzz_sweep") {
    const summary = await RedTeamEngine.runFuzzSweep({
      targetPersonas: (body.targetPersonas as string[]) ?? ["saksee"],
      vectors: body.vectors as AttackVector[] | undefined,
    });
    return { summary, verdicts: RedTeamEngine.getVerdicts() };
  }

  if (action === "test_payload") {
    const { payload } = body as Record<string, unknown>;
    if (!payload || !(payload as Record<string, unknown>).rawPayload) {
      throw new Error("Missing payload object or rawPayload string");
    }
    return { verdict: RedTeamEngine.evaluatePayloadDefense(payload as FuzzingPayload) };
  }

  throw new Error(`Invalid action: ${action}`);
});
