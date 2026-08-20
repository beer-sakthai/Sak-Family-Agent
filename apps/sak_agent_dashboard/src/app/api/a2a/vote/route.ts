import { ApiError, createApiHandler, createMutationHandler } from "@/lib/api/handler";
import { A2AConsensusSession, A2AVoteBallot, VoteChoice } from "@/lib/a2a/types";

export const dynamic = "force-dynamic";

// Module-level session store (same behavior as original)
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

export const GET = createApiHandler("/api/a2a/vote", async () => ({
  sessions: activeSessions,
  timestamp: new Date().toISOString(),
}));

export const POST = createMutationHandler("/api/a2a/vote", async (body) => {
  const { sessionId, persona, choice, rationale } = body as Record<string, unknown>;

  if (!sessionId || !persona || !choice) {
    throw new ApiError(400, "Missing required voting fields");
  }

  const validChoices: VoteChoice[] = ["approve", "reject", "abstain", "veto"];
  const voteChoice = String(choice).toLowerCase() as VoteChoice;
  if (!validChoices.includes(voteChoice)) {
    throw new ApiError(400, `Invalid choice: ${choice}`);
  }

  const ballot: A2AVoteBallot = {
    sessionId: String(sessionId),
    persona: String(persona),
    choice: voteChoice,
    weight: 1.0,
    rationale: rationale ? String(rationale) : undefined,
    timestamp: new Date().toISOString(),
  };

  let session = activeSessions.find((s) => s.sessionId === sessionId);
  if (!session) {
    const validDomains = ["security", "vision", "content", "devops", "governance", "general"] as const;
    const domainStr = String(body.domain ?? "general");
    const domain = (validDomains.includes(domainStr as any) ? domainStr : "general") as A2AConsensusSession["domain"];

    session = {
      sessionId: String(sessionId),
      topic: String(body.topic ?? "Multi-Agent Consensus Vote"),
      domain,
      quorumThreshold: 0.6,
      resolved: false,
      outcome: "PENDING",
      createdAt: new Date().toISOString(),
      ballots: [],
    };
    activeSessions.push(session);
  }

  session.ballots.push(ballot);
  return { session };
});
