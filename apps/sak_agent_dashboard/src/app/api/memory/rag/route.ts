import { NextRequest, NextResponse } from "next/server";
import { getKnowledgeGraphData, getTelegramBridgeData } from "@/lib/memoryRag";

export async function GET() {
  try {
    const graph = getKnowledgeGraphData();
    const telegram = getTelegramBridgeData();
    return NextResponse.json({
      success: true,
      graph,
      telegram,
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: (error as Error).message },
      { status: 500 }
    );
  }
}

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
    return NextResponse.json(
      { success: false, error: (error as Error).message },
      { status: 500 }
    );
  }
}
