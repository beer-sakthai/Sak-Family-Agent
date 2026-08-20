import { ApiError, createApiHandler, createMutationHandler } from "@/lib/api/handler";
import { MutationEngine } from "@/lib/mutation/mutationEngine";
import { SelfHealingTestGenerator } from "@/lib/mutation/selfHealingTestGenerator";
import { MutationOperator } from "@/lib/mutation/types";

export const GET = createApiHandler("/api/mutation", async (ctx) => {
  const action = ctx.params["action"] ?? "all";
  const sweepId = ctx.params["sweepId"];

  if (action === "sweeps") return { sweeps: MutationEngine.getRecentSweeps() };
  if (action === "mutants") return { mutants: MutationEngine.getMutants(sweepId) };

  return {
    data: {
      sweeps: MutationEngine.getRecentSweeps(),
      mutants: MutationEngine.getMutants(sweepId),
    },
  };
});

export const POST = createMutationHandler("/api/mutation", async (body) => {
  const { action } = body as Record<string, unknown>;

  if (action === "sweep") {
    const defaultOperators: MutationOperator[] = [
      "conditional_inversion",
      "boolean_flip",
      "arithmetic_boundary",
      "return_value_substitution",
    ];
    const operators = Array.isArray(body.operators)
      ? (body.operators as MutationOperator[])
      : defaultOperators;

    const summary = await MutationEngine.runSweep({
      targetFiles: (body.targetFiles as string[]) ?? ["src/lib/eval/evalEngine.ts", "src/lib/cache/semanticCacheEngine.ts"],
      operators,
      timeoutMs: Number(body.timeoutMs) || 5000,
      concurrency: Number(body.concurrency) || 2,
    });
    return { summary, mutants: MutationEngine.getMutants(summary.sweepId) };
  }

  if (action === "heal") {
    const mutantId = String(body.mutantId ?? "");
    const mutant = MutationEngine.getMutants().find((m) => m.id === mutantId);
    if (!mutant) throw new ApiError(404, `Mutant ${mutantId} not found`);
    return { healResult: SelfHealingTestGenerator.synthesizeHealerTest(mutant) };
  }

  if (action === "batch_heal") {
    const mutants = MutationEngine.getMutants(body.sweepId as string | undefined);
    return { healResults: SelfHealingTestGenerator.batchHeal(mutants) };
  }

  throw new ApiError(400, `Invalid action: ${action}`);
});
