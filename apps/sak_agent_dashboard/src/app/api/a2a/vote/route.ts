import { NextRequest, NextResponse } from "next/server";
import { A2AConsensusSession, A2AVoteBallot } from "@/lib/a2a/types";

export const dynamic = "force-dynamic";

// In-memory mock sessions for development/testing
const activeSessions: A2AConsensusSession[] = [
  {
    sessionId: "vote_seed_01",
    topic: "Approve Self-Healing Multi-Agent Recovery Protocol PR",
    domain: "security",
    quorumThreshold: 0.6,
    resolved: true,
    outcome: "APPROVED",
    createdAt: new Date(Date.now() - 3600000).toISOString(),
    ballots: [
      {
        sessionId: "vote_seed_01",
        persona: "sakking",
        choice: "approve",
        weight: 2.0,
        rationale: "AST guardrails and PBKDF2 hashing pass verification.",
        timestamp: new Date(Date.now() - 3500000).toISOString(),
      },
      {
        sessionId: "vote_seed_01",
        persona: "sakjules",
        choice: "approve",
        weight: 2.0,
        rationale: "CI matrix and mutation tests 100% green.",
        timestamp: new Date(Date.now() - 3400000).toISOString(),
      },
      {
        sessionId: "vote_seed_01",
        persona: "sakthai",
        choice: "approve",
        weight: 1.5,
        rationale: "Architecture aligns with v2.6.0 roadmap.",
        timestamp: new Date(Date.now() - 3300000).toISOString(),
      },
    ],
  },
];

export async function GET() {
  return NextResponse.json({
    success: true,
    sessions: activeSessions,
    timestamp: new Date().toISOString(),
  });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { sessionId, persona, choice, rationale } = body;

    if (!sessionId || !persona || !choice) {
      return NextResponse.json({ error: "Missing required voting fields" }, { status: 400 });
    }

    const ballot: A2AVoteBallot = {
      sessionId,
      persona,
      choice,
      weight: 1.0,
      rationale,
      timestamp: new Date().toISOString(),
    };

    let session = activeSessions.find((s) => s.sessionId === sessionId);
    if (!session) {
      session = {
        sessionId,
        topic: body.topic || "Multi-Agent Consensus Vote",
        domain: body.domain || "general",
        quorumThreshold: 0.6,
        resolved: false,
        outcome: "PENDING",
        createdAt: new Date().toISOString(),
        ballots: [],
      };
      activeSessions.push(session);
    }

    session.ballots.push(ballot);
    return NextResponse.json({ success: true, session });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message || "Internal server error" }, { status: 500 });
  }
}
