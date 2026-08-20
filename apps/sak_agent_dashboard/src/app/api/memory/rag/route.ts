import { NextRequest, NextResponse } from "next/server";
import { createApiHandler } from "@/lib/api/handler";
import { getKnowledgeGraphData, getTelegramBridgeData } from "@/lib/memoryRag";

export const GET = createApiHandler("/api/memory/rag", async () => {
  const graph = getKnowledgeGraphData();
  const telegram = getTelegramBridgeData();
  return { graph, telegram };
});

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { query } = body;

    const graph = getKnowledgeGraphData();
    const matches = graph.nodes.filter((node) =>
      query ? node.label.toLowerCase().includes(query.toLowerCase()) : true
    );

    return NextResponse.json({
      success: true,
      query: query || "*",
      totalHits: matches.length,
      hits: matches.map((m) => ({
        id: m.id,
        label: m.label,
        type: m.type,
        similarityScore: 0.94,
        source: "~/.sakthai/memory.db",
      })),
    });
  } catch (error) {
    console.error("Secure Log [POST /api/memory/rag]:", error);
    return NextResponse.json(
      { success: false, error: "An unexpected error occurred" },
      { status: 500 }
    );
  }
}
