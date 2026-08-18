import {
  AutoCycleData,
  AutoCycleSkill,
  CyclePersonaDispatch,
  CycleStage,
} from "./types";

/**
 * Mirrors personas/sakthai/sakthai/cycle/stages.py — the STAGES tuple is the
 * source of truth. Keep goal/commands/guidance byte-aligned with it.
 */
const STAGES: CycleStage[] = [
  {
    stage: "dream",
    number: 1,
    goal: "Define the vision or task",
    commands: ["memory show"],
    guidance: "Explore options and recall past context; don't implement yet.",
  },
  {
    stage: "hope",
    number: 2,
    goal: "Engineer a solution",
    commands: ["learn"],
    guidance:
      "Propose concrete approaches and capture key decisions with `sakthai learn`.",
  },
  {
    stage: "care",
    number: 3,
    goal: "Refine quality — concurrency and performance",
    commands: ["learn"],
    guidance:
      "Audit correctness, race conditions, and performance; record findings.",
  },
  {
    stage: "joy",
    number: 4,
    goal: "Package and ship",
    commands: ["memory stats"],
    guidance: "Focus on packaging and CI; celebrate what shipped.",
  },
  {
    stage: "trust",
    number: 5,
    goal: "Secure the foundation",
    commands: ["doctor"],
    guidance: "Run `sakthai doctor`, check boundaries, and verify idempotency.",
  },
  {
    stage: "growth",
    number: 6,
    goal: "Learn and grow",
    commands: ["memory consolidate"],
    guidance: "Capture learnings into memory, then loop back to Dream.",
  },
];

const PERSONAS: CyclePersonaDispatch[] = [
  { persona: "SakKing", liveHome: "/opt/data" },
  { persona: "SakThai", liveHome: "/opt/data/profiles/sakthai", lead: true },
  { persona: "SakSee", liveHome: "/opt/data/profiles/saksee" },
  { persona: "SakSit", liveHome: "/opt/data/profiles/saksit" },
  { persona: "SakTan", liveHome: "/opt/data/profiles/saktan" },
  { persona: "SakJules", liveHome: "/opt/data/profiles/sakjules" },
];

const SKILLS: AutoCycleSkill[] = [
  {
    name: "Sak-auto-cycle-loop",
    path: "personas/shared/skills/Sak-auto-cycle-loop/SKILL.md",
    layer: "shared",
    purpose:
      "sakthai-native. Injected with `--with-skills`. On completing Growth it records the round's lesson via `learn --tag growth`, calls `cycle next` to re-enter Dream, and starts the next queued task instead of ending the session. Tracks rounds in-session and stops cleanly after the 3rd Growth even if budget remains.",
  },
  {
    name: "Sak-family-auto-cycle",
    path: ".claude/skills/Sak-family-auto-cycle/SKILL.md",
    layer: "claude-code",
    purpose:
      "Claude Code orchestrator. Dispatches six Agent tool calls in a single message — true parallelism, one per persona — then writes one consolidated report. Adds no outer loop of its own: round-bounding already happens per-persona inside the shared skill.",
  },
];

export function getAutoCycleData(): AutoCycleData {
  return {
    overview: {
      title: "Sak Family Auto-Cycle",
      description:
        "The six-stage Dream → Hope → Care → Joy → Trust → Growth cycle is manual and single-track on its own: one persona, one `sakthai run`, one pass, then it stops. The auto-cycle is two composing skills that fix both halves — a persona sustains multiple rounds in one invocation, and one command fans out to all six personas in parallel, each sustaining their own bounded cycle.",
      specPath: "docs/superpowers/specs/2026-07-08-sak-family-auto-cycle-design.md",
      planPath: "docs/superpowers/plans/2026-07-08-sak-family-auto-cycle.md",
      skillPath: ".claude/skills/Sak-family-auto-cycle/SKILL.md",
    },
    stages: STAGES,
    personas: PERSONAS,
    skills: SKILLS,
    roundCap: 3,
    safetyRule: {
      headline: "Default to a dry, throwaway run — this is not optional",
      body:
        "Every one of the six dispatched `sakthai run` commands gets `--dry-run` appended and its own fresh `SAKTHAI_HOME=$(mktemp -d)`, never a real path from the dispatch table. Test mode itself needs no permission — only switching to live does. Asking the user before every dispatch, even the throwaway one, is a different failure (stalling on something that was never risky), not a stricter version of the rule.",
      testCommand:
        'SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "<task>" \\\n  --with-skills Sak-auto-cycle-loop \\\n  --provider anthropic --max-iterations N --max-seconds M \\\n  --dry-run',
      liveAuthorizationPhrases: [
        '"do a live run"',
        '"this is for real, no dry-run"',
        '"point it at the real homes"',
      ],
      nonAuthorizationPhrases: [
        '"run the family auto-cycle"',
        '"get them working together"',
        '"just run it"',
        '"go"',
        "a stated deadline",
        '"they clearly want it to actually do something" (your own reasoning)',
      ],
      baselineEvidence:
        "In 5 of 5 independent baseline runs of this exact scenario with no skill loaded, the dispatching agent planned to write directly into the real, live persona homes — /opt/data and /opt/data/profiles/<name> — with no --dry-run and no throwaway home. Not one of the five paused to consider whether a safe mode should come first.",
    },
    dispatchNote:
      "The response is one message containing six Agent tool calls, dispatched together — not one at a time, not 'first SakKing, then check results, then SakThai'. Six subagents running concurrently is what 'the family working together' means; checking one result before starting the next is the opposite of it.",
    errorHandling:
      "A persona that fails — auth error, crash, blocked task, hits --max-seconds mid-round — reports its own failure in the consolidated summary. One persona failing does not fail the other five; the orchestrator always reports all six outcomes, whether success, partial, or failure.",
    resolvedGap:
      "Resolved 2026-07-13: personas/shared/skills/ is now on the runtime's skill-discovery path (default_skill_roots() in skills.py), so --with-skills Sak-auto-cycle-loop resolves without a compose/sync step. --dry-run now also validates --with-skills names and exits non-zero on unresolved ones, so a clean dry-run is real evidence the skill will inject.",
    cliCommands: [
      { command: "sakthai cycle status", purpose: "Show the persona's current stage." },
      { command: "sakthai cycle next", purpose: "Advance to the next stage (Growth wraps to Dream)." },
      { command: "sakthai cycle set <stage>", purpose: "Jump directly to a named stage." },
      { command: "sakthai cycle list", purpose: "List all six stages with their goals." },
    ],
  };
}
