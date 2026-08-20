import { ApiError, createApiHandler, createMutationHandler } from "@/lib/api/handler";
import { SemanticCacheEngine } from "@/lib/cache/semanticCacheEngine";
import { CacheLookupQuery } from "@/lib/cache/types";

export const GET = createApiHandler("/api/cache", async (ctx) => {
  const action = ctx.params["action"] ?? "all";

  if (action === "analytics") {
    return { analytics: SemanticCacheEngine.getAnalytics() };
  }

  if (action === "entries") {
    return { entries: SemanticCacheEngine.getAllEntries() };
  }

  return {
    data: {
      analytics: SemanticCacheEngine.getAnalytics(),
      entries: SemanticCacheEngine.getAllEntries(),
    },
  };
});

export const POST = createMutationHandler("/api/cache", async (body) => {
  const { action } = body as Record<string, unknown>;

  if (action === "lookup") {
    const query: CacheLookupQuery = {
      prompt: String(body.prompt ?? ""),
      personaSlug: body.personaSlug as string | undefined,
      model: body.model as string | undefined,
      minSimilarity: body.minSimilarity ? parseFloat(String(body.minSimilarity)) : undefined,
    };
    if (!query.prompt.trim()) throw new ApiError(400, "prompt is required");
    return { result: SemanticCacheEngine.lookup(query) };
  }

  if (action === "store") {
    const { prompt, response, personaSlug, model, ttlSeconds, similarityThreshold } = body as Record<string, unknown>;
    if (!prompt || !response) throw new ApiError(400, "prompt and response are required");
    const entry = SemanticCacheEngine.store(
      String(prompt),
      String(response),
      personaSlug as string | undefined,
      model as string | undefined,
      ttlSeconds as number | undefined,
      similarityThreshold as number | undefined,
    );
    return { entry };
  }

  if (action === "invalidate") {
    const count = SemanticCacheEngine.invalidate(body.id as string | undefined, body.personaSlug as string | undefined);
    return { deletedCount: count };
  }

  if (action === "clear") {
    return { deletedCount: SemanticCacheEngine.invalidate() };
  }

  throw new ApiError(400, `Invalid action: ${action}`);
});
