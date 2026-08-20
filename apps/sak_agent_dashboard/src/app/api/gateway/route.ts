import { ApiError, createApiHandler, createMutationHandler } from "@/lib/api/handler";

const PERSONA_PROFILES: Record<string, { role: string; specialization: string; defaultCharge: number }> = {
  sakthai: { role: "SakThai · Core Reasoning & Adaptive Coding", specialization: "General reasoning, algorithm optimization, self-healing code", defaultCharge: 100 },
  sakking: { role: "SakKing · Architectural Vision & Strategic Design", specialization: "System architecture, high-level roadmaps, visual pipelines", defaultCharge: 95 },
  saksee: { role: "SakSee · Deep Research & Visual Intelligence", specialization: "Academic papers, web investigation, presentation decks", defaultCharge: 90 },
  saksit: { role: "SakSit · Creative Copywriting & Narrative Content", specialization: "Marketing copy, narrative stories, tone refinement", defaultCharge: 85 },
  sakjules: { role: "SakJules · Master of Automation & CI/CD", specialization: "DevOps, GitHub Actions, security patching, Docker & testing", defaultCharge: 100 },
  saktan: { role: "SakTan · Daily Operations & Triage Master", specialization: "Scheduling, logging, instant service quotes & triage", defaultCharge: 90 },
};

const KEYWORD_MAP: Record<string, { intent: string; persona: string; confidence: number }> = {
  ci: { intent: "automation_ci", persona: "sakjules", confidence: 0.98 },
  workflow: { intent: "automation_ci", persona: "sakjules", confidence: 0.95 },
  docker: { intent: "automation_ci", persona: "sakjules", confidence: 0.95 },
  deploy: { intent: "automation_ci", persona: "sakjules", confidence: 0.92 },
  research: { intent: "research", persona: "saksee", confidence: 0.96 },
  paper: { intent: "research", persona: "saksee", confidence: 0.94 },
  arxiv: { intent: "research", persona: "saksee", confidence: 0.98 },
  slide: { intent: "presentation", persona: "saksee", confidence: 0.95 },
  powerpoint: { intent: "presentation", persona: "saksee", confidence: 0.95 },
  copy: { intent: "copywriting", persona: "saksit", confidence: 0.90 },
  marketing: { intent: "copywriting", persona: "saksit", confidence: 0.92 },
  architecture: { intent: "architecture", persona: "sakking", confidence: 0.94 },
  schedule: { intent: "operations", persona: "saktan", confidence: 0.90 },
  quote: { intent: "operations", persona: "saktan", confidence: 0.92 },
};

export const GET = createApiHandler("/api/gateway", async () => ({
  personas: PERSONA_PROFILES,
  status: "online",
  activeSessions: 6,
}));

export const POST = createMutationHandler("/api/gateway", async (body) => {
  const message = (String(body.message ?? "")).toLowerCase().trim();
  const preferred = body.preferred_persona as string | undefined;

  if (!message) throw new ApiError(400, "Message cannot be empty");

  let selectedPersona = "sakthai";
  let detectedIntent = "core_reasoning";
  let confidence = 0.75;
  const matchedKeywords: string[] = [];

  for (const p of Object.keys(PERSONA_PROFILES)) {
    if (message.includes(`@${p}`)) {
      selectedPersona = p;
      detectedIntent = `explicit_${p}`;
      confidence = 1.0;
      matchedKeywords.push(`@${p}`);
      break;
    }
  }

  if (matchedKeywords.length === 0) {
    for (const [kw, meta] of Object.entries(KEYWORD_MAP)) {
      if (message.includes(kw)) {
        selectedPersona = meta.persona;
        detectedIntent = meta.intent;
        confidence = meta.confidence;
        matchedKeywords.push(kw);
        break;
      }
    }
  }

  if (preferred && PERSONA_PROFILES[preferred]) selectedPersona = preferred;

  const profile = PERSONA_PROFILES[selectedPersona] ?? PERSONA_PROFILES.sakthai;

  return {
    selectedPersona,
    roleDeclaration: profile.role,
    intent: detectedIntent,
    confidence,
    matchedKeywords,
    chargeLevel: profile.defaultCharge,
    reply: `${profile.role}\n\nProcessed query with specialized intent '${detectedIntent}' (confidence: ${(confidence * 100).toFixed(0)}%).`,
  };
});
