import { SelfEvolutionData, PromptEvolutionItem, LearningJournalEntry } from "./types";

export const SAMPLE_PROMPT_EVOLUTIONS: PromptEvolutionItem[] = [
  {
    id: "evo_sakthai_01",
    personaSlug: "sakthai",
    timestamp: "2026-08-14T22:15:00Z",
    originalSnippet: "You are SakThai. Help the user orchestrate agent pipelines.",
    evolvedSnippet: "You are SakThai, the primary orchestrator. Decompose multi-step intents into bounded stages and assign appropriate personas with fallback to Ollama ($0.00).",
    rationale: "Eliminated prompt vagueness, established clear task boundary rules, and added zero-cost fallback cascade.",
    performanceDelta: "+14.2% Execution Accuracy",
  },
  {
    id: "evo_sakjules_02",
    personaSlug: "sakjules",
    timestamp: "2026-08-15T01:10:00Z",
    originalSnippet: "Identify yourself as SakJules. Run build commands.",
    evolvedSnippet: "Identify yourself with: **SakJules · Master of Automation & CI/CD.** Always add `/* turbopackIgnore: true */` to dynamic filesystem probes in Next.js Turbopack.",
    rationale: "Prevents full-workspace dynamic tracing warnings and guarantees zero-warning production builds.",
    performanceDelta: "Zero-Warning Turbopack Build Achieved",
  },
  {
    id: "evo_sakking_03",
    personaSlug: "sakking",
    timestamp: "2026-08-15T01:45:00Z",
    originalSnippet: "Review code changes for bugs.",
    evolvedSnippet: "Perform deep AST inspection on Python & TypeScript changes. Reject any unmasked secret access or unbound shell forks before committing.",
    rationale: "Zero-tolerance security enforcement preventing credential leakage.",
    performanceDelta: "100% Sentinel Gate Pass Rate",
  },
];

export const SAMPLE_LEARNING_JOURNAL: LearningJournalEntry[] = [
  {
    id: "lj_001",
    timestamp: "2026-08-14T23:40:00Z",
    persona: "SakJules",
    triggerEvent: "Turbopack dynamic tracing warning in speckit.ts",
    lessonLearned: "Dynamic filesystem checks cause full project tracing unless annotated with /* turbopackIgnore: true */.",
    remediationApplied: true,
  },
  {
    id: "lj_002",
    timestamp: "2026-08-15T01:25:00Z",
    persona: "SakKing",
    triggerEvent: "Multiple matching elements in Vitest string queries",
    lessonLearned: "Avoid exact getByText when tokens appear in both badges and body copy; use getAllByText or specific data-testid.",
    remediationApplied: true,
  },
  {
    id: "lj_003",
    timestamp: "2026-08-15T02:10:00Z",
    persona: "SakTan",
    triggerEvent: "SQLite WAL lock contention during simultaneous multi-agent memory writes",
    lessonLearned: "Use busy_timeout=5000 and write-ahead log (WAL) mode for persistent multi-persona consensus.",
    remediationApplied: true,
  },
];

export function getSelfEvolutionData(): SelfEvolutionData {
  return {
    round: 4,
    evolutions: SAMPLE_PROMPT_EVOLUTIONS,
    journalEntries: SAMPLE_LEARNING_JOURNAL,
    mutationCoveragePct: 94.8,
    lastWrapTimestamp: new Date().toISOString(),
  };
}
