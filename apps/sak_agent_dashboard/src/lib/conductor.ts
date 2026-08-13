import {
  ConductorArtifact,
  ConductorCommand,
  ConductorData,
  ConductorHost,
} from "./types";

const HOSTS: ConductorHost[] = [
  {
    id: "antigravity",
    name: "Antigravity CLI (agy)",
    installCommand:
      "agy plugins install https://github.com/gemini-cli-extensions/conductor",
    note: "Primary integration — recommended by the plugin authors.",
    primary: true,
  },
  {
    id: "claude-code",
    name: "Claude Code",
    installCommand:
      "/plugin marketplace add gemini-cli-extensions/conductor\n/plugin install conductor",
    note: "Two-step install via the Claude Code plugin marketplace.",
  },
  {
    id: "live-symlink",
    name: "Live development",
    installCommand:
      "ln -sfn \"$(pwd)\" ~/.gemini/config/plugins/conductor",
    note: "Symlink the cloned repo into the Gemini plugin dir so edits are picked up without reinstalling.",
  },
];

const COMMANDS: ConductorCommand[] = [
  {
    slash: "/conductor:conductor-setup",
    purpose:
      "Scaffold the project — creates product.md, product-guidelines.md, tech-stack.md, and workflow.md in ./conductor/.",
    category: "setup",
  },
  {
    slash: "/conductor:conductor-new-track",
    purpose:
      "Start a new feature or bug track. Generates track-scoped spec.md and plan.md the agent then implements against.",
    category: "track",
  },
  {
    slash: "/conductor:conductor-implement",
    purpose:
      "Execute the current track's plan task-by-task. The agent works through the plan in order, respecting the review gates.",
    category: "implement",
  },
  {
    slash: "/conductor:conductor-status",
    purpose:
      "Show progress across tracks — which specs are drafted, which plans are approved, which tasks are done or in flight.",
    category: "status",
  },
  {
    slash: "/conductor:conductor-revert",
    purpose:
      "Safely undo features, phases, or individual tasks. Git-aware — goes beyond a simple commit revert.",
    category: "revert",
  },
  {
    slash: "/conductor:conductor-review",
    purpose:
      "Audit completed work against product-guidelines.md and the track's own spec. Flags drift and open follow-ups.",
    category: "review",
  },
];

const ARTIFACTS: ConductorArtifact[] = [
  {
    path: "conductor/product.md",
    purpose: "One-liner product vision + user personas. Written once at setup, edited rarely.",
    scope: "project",
  },
  {
    path: "conductor/product-guidelines.md",
    purpose:
      "Non-negotiables: coding standards, review rules, UX principles. Consulted by every /conductor:conductor-review.",
    scope: "project",
  },
  {
    path: "conductor/tech-stack.md",
    purpose:
      "Fixed stack decisions — frameworks, hosting, key libraries. The agent avoids introducing anything not listed.",
    scope: "project",
  },
  {
    path: "conductor/workflow.md",
    purpose:
      "Team conventions for git, PRs, testing, and release. Guides how the implement step commits work.",
    scope: "project",
  },
  {
    path: "conductor/tracks/<track>/spec.md",
    purpose:
      "Track-scoped specification: problem, users, acceptance criteria. Produced by /conductor:conductor-new-track.",
    scope: "track",
  },
  {
    path: "conductor/tracks/<track>/plan.md",
    purpose:
      "Ordered task list the agent works through under /conductor:conductor-implement. Review-gated between phases.",
    scope: "track",
  },
];

const WORKFLOW: string[] = [
  "conductor-setup → project artifacts (product.md, product-guidelines.md, tech-stack.md, workflow.md).",
  "conductor-new-track → spec.md drafted for a specific feature or bug, reviewed by the user.",
  "conductor-new-track → plan.md generated from the approved spec, reviewed by the user.",
  "conductor-implement → tasks executed in order, with review gates between phases.",
  "conductor-status → progress readout across all tracks at any point.",
  "conductor-review → audit the completed work against guidelines + spec, catching drift.",
  "conductor-revert → git-aware rollback of a feature, phase, or single task if something needs to unwind.",
];

export function getConductorData(): ConductorData {
  return {
    overview: {
      title: "Conductor — Spec-Driven Dev for Agents",
      description:
        "A plugin that turns an AI coding agent (primarily Antigravity, also Claude Code) into a proactive project manager. It enforces a spec → plan → implement → review cycle backed by persistent project artifacts, so the agent doesn't drift from the product's intent as tasks land.",
      repoUrl: "https://github.com/gemini-cli-extensions/conductor",
      methodology: "Spec-Driven Development (SDD)",
    },
    hosts: HOSTS,
    commands: COMMANDS,
    artifacts: ARTIFACTS,
    workflow: WORKFLOW,
    liveDevCommand:
      "ln -sfn \"$(pwd)\" ~/.gemini/config/plugins/conductor",
  };
}
