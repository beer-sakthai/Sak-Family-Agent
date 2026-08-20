import { ApiError, createApiHandler, createMutationHandler } from "@/lib/api/handler";
import { hfEcosystemEngine } from "@/lib/hfEcosystemEngine";

export const dynamic = "force-dynamic";

export const GET = createApiHandler("/api/hf/ecosystem", async () => {
  const summary = hfEcosystemEngine.getEcosystemSummary();
  return { data: { summary, timestamp: new Date().toISOString() } };
});

export const POST = createMutationHandler("/api/hf/ecosystem", async (body) => {
  const { action, repoId, content, factoryRebuild } = body as Record<string, unknown>;

  if (action === "validate_card" && repoId && content) {
    return { result: hfEcosystemEngine.validateCard(String(repoId), String(content)) };
  }

  if (action === "diagnose_space" && repoId) {
    return { diagnostic: hfEcosystemEngine.diagnoseSpace(String(repoId)) };
  }

  if (action === "remediate_space" && repoId) {
    return { outcome: hfEcosystemEngine.remediateSpace(String(repoId), !!factoryRebuild) };
  }

  if (action === "preview_all_cards") {
    return { previews: hfEcosystemEngine.previewAllCards() };
  }

  throw new ApiError(400, "Invalid action or missing parameters");
});
