import { ApiError, createMutationHandler } from "@/lib/api/handler";

export const dynamic = "force-dynamic";

export const POST = createMutationHandler("/api/memory/vector", async (body) => {
  const { queryText, limit = 5 } = body as { queryText?: string; limit?: number };
  if (!queryText) throw new ApiError(400, "queryText is required");

  const mockResults = [
    {
      id: "mem_obs_01",
      score: 0.942,
      metadata: {
        category: "architecture",
        persona: "sakthai",
        content: `Indexed memory for query: ${queryText}`,
        timestamp: new Date().toISOString(),
      },
    },
    {
      id: "mem_fact_02",
      score: 0.887,
      metadata: {
        category: "security",
        persona: "sakking",
        content: "AST guardrails reject control characters and malicious shell injections.",
        timestamp: new Date(Date.now() - 3600000).toISOString(),
      },
    },
  ];

  return {
    query: queryText,
    results: mockResults.slice(0, Number(limit)),
    latencyMs: 1.4,
  };
});
