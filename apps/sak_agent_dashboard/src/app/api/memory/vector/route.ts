import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { queryText, limit = 5 } = body;

    if (!queryText) {
      return NextResponse.json({ error: "queryText is required" }, { status: 400 });
    }

    // Mock search results for dashboard demo
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

    return NextResponse.json({
      success: true,
      query: queryText,
      results: mockResults.slice(0, limit),
      latencyMs: 1.4,
    });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message || "Internal server error" }, { status: 500 });
  }
}
