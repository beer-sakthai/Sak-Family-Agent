---
name: superpowers-unified
description: Use when building features, fixing bugs, refactoring, planning architecture, running tests, managing git branches, reviewing code, authoring skills, or diagnosing agent workflow failures.
---

# Superpowers Unified Engineering Workflow

A single-file consolidation of all 15 `obra/superpowers` engineering skills into one portable, cross-agent methodology. Follow the matching workflow stage whenever a trigger applies.

## 1. Bootstrap & Routing (`using-superpowers`)

Before writing code, editing files, or declaring work complete, identify which phase below matches the current task and follow its gates.

| Current Situation | Active Module(s) |
| :--- | :--- |
| New feature, architecture change, or ambiguous request | **2. Brainstorming** -> **3. Git Worktrees** -> **4. Writing Plans** |
| Approved plan ready to implement | **5. Executing Plans** (inline) OR **6. Subagent Dev** / **7. Parallel Agents** |
| Writing or modifying any production code | **8. Test-Driven Development** |
| Bug, test failure, crash, or unexpected behavior | **9. Systematic Debugging** |
| Task or milestone ready for inspection | **10. Requesting Code Review** / **11. Receiving Code Review** |
| Ready to report success or close a task | **12. Verification Before Completion** -> **13. Finishing a Branch** |
| Workflow missed a gate, stalled, or burned excessive tokens | **14. Diagnosing Superpowers** |
| Creating or editing a `SKILL.md` instruction file | **15. Writing Skills** |

**Proportionality Rule:** For pure Q&A, read-only audits, or single-line typo/comment fixes with zero behavioral impact, answer directly without triggering full design/worktree ceremony. For all behavioral code changes, enforce the Iron Laws below.

### The Four Iron Laws
1. **NO IMPLEMENTATION BEFORE DESIGN APPROVAL** on non-trivial features.
2. **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.**
3. **NO FIXES WITHOUT ROOT-CAUSE INVESTIGATION FIRST.**
4. **NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**

---

## 2. Requirements & Design (`brainstorming`)

Never jump straight into code when intent, constraints, or edge cases are unclear.

1. **Inspect context first:** Read relevant files, architecture, and recent git history silently before asking questions.
2. **Clarify one topic at a time:** Ask concise, high-signal questions (prefer multiple-choice options with a recommended default) to nail down goals, constraints, non-goals, and edge cases.
3. **Propose 2–3 approaches:** Present trade-offs clearly and state your recommendation with reasoning.
4. **Write a concise design spec:** Summarize architecture, data flow, interfaces, error handling, and test strategy (e.g., in `docs/specs/<topic>.md` when working in a repo).
5. **Hard Gate:** Obtain explicit user approval of the design before creating an implementation plan or editing production code.

---

## 3. Isolated Workspaces (`using-git-worktrees`)

Isolate feature work and risky refactors from the main branch whenever working inside a git repository.

1. **Select a clean directory:** Prefer `.worktrees/<branch>` (project-local) or a dedicated sibling worktree directory.
2. **Verify `.gitignore`:** If using a project-local worktree directory, confirm it is gitignored before creating it.
3. **Create branch & worktree:** Run `git worktree add <path> -b <branch-name>`.
4. **Initialize & verify baseline:** Install dependencies and run the existing test suite. Report any pre-existing failures before making changes—never mask baseline failures.

---

## 4. Micro-Task Planning (`writing-plans`)

Break an approved design into small, verifiable steps so execution never drifts.

1. **Scope each task to 2–5 minutes:** One focused outcome per task.
2. **Specify exact targets:** List exact file paths to create or modify, expected interfaces/behaviors, and the exact command + expected output that proves completion.
3. **Avoid code duplication bloat:** Describe interfaces, contracts, and edge cases cleanly rather than pasting full verbatim source files into Markdown unless exact boilerplate is critical.
4. **Save the plan:** Write to `docs/plans/YYYY-MM-DD-<topic>.md` (or present inline if outside a repo) and confirm execution mode (inline vs. subagents) with the user.

---

## 5. Inline Execution (`executing-plans`)

Use when executing a plan directly in the current session (chosen by user, tight token budget, or no subagent tool available).

1. **Review the whole plan first:** Flag ambiguities, missing prerequisites, or contradictions before editing anything.
2. **Execute sequentially:** Work one task at a time using **Section 8 (TDD)**.
3. **Verify per task:** Run the task's verification command and confirm clean output before moving to the next task.
4. **Checkpoint in batches:** After each logical milestone (or whenever hitting an unexpected blocker), report exact progress and verification output; stop immediately on blockers instead of guessing.

---

## 6. Subagent Orchestration (`subagent-driven-development`)

Use when subagent dispatch is available and you want clean context isolation across multi-task plans.

1. **One fresh subagent per task:** Never pass your entire messy conversation history. Provide a crisp brief containing: task goal, exact file paths, relevant spec excerpts, constraints, and verification commands.
2. **Two-stage review after each task:**
   * **Stage A — Spec Compliance:** Verify the implementation matches every requirement with nothing missing and no unrequested scope creep.
   * **Stage B — Code Quality:** Check readability, edge cases, test coverage, and maintainability.
3. **Fix before advancing:** If either review flags Critical or Important issues, fix and re-verify before dispatching the next task.

---

## 7. Parallel Dispatch (`dispatching-parallel-agents`)

Use **only** when facing 2+ independent failures, investigations, or tasks with **zero shared mutable state** and **no overlapping file edits**.

1. **Confirm independence:** Verify tasks do not modify the same files, shared fixtures, or database state.
2. **Scope each agent narrowly:** Define exact problem statement, allowed files/scope, and expected return format.
3. **Integrate & verify sequentially:** Once parallel agents return, inspect all summaries for conflicts and run the full integrated test suite.

---

## 8. Test-Driven Development (`test-driven-development`)

**Iron Law:** `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.`

1. **RED:** Write the smallest unit or integration test describing one desired behavior. Run it and **observe it fail for the expected reason** (missing function/assertion failure, not a syntax or import typo).
2. **GREEN:** Write the minimal production code required to make that test pass. Do not add speculative features or extra abstractions.
3. **REFACTOR:** Clean up duplication, naming, and structure while keeping all tests green.
4. **Discipline Check:** If you wrote production code before writing the test, delete the unverified code and restart from RED. Never retroactively write tests just to rubber-stamp existing code.

---

## 9. Systematic Debugging (`systematic-debugging`)

**Iron Law:** `NO FIXES WITHOUT ROOT-CAUSE INVESTIGATION FIRST.`

### Phase 1: Root-Cause Investigation
* Read full error messages, stack traces, and logs completely.
* Reproduce the failure reliably before touching code.
* Inspect recent diffs (`git diff`, `git log`), config, and environment state.
* Trace the bad value backward to its true origin (root cause), not merely where it surfaced.

### Phase 2: Pattern Analysis
* Compare failing code against a working equivalent in the codebase.
* List every concrete difference in inputs, state, timing, or dependencies.

### Phase 3: Hypothesis & Single-Variable Test
* State one falsifiable hypothesis: *"X fails because Y; changing Z will produce W."*
* Test with the smallest possible change or diagnostic probe. Revert failed probes immediately.

### Phase 4: Fix & Regression Lock
* Write a failing regression test that reproduces the exact bug (**Section 8**).
* Implement the minimal root-cause fix and verify the full suite passes.
* **Two-Strike Escalation Rule:** If two fix attempts fail, **STOP**. Do not guess a third patch. Re-examine your architectural assumptions and report findings to the user.

---

## 10. Requesting Code Review (`requesting-code-review`)

Trigger after completing a milestone, before merging, or after a complex bug fix.

1. **Gather clean diff context:** Capture the exact git range (`git diff <base>..HEAD`), design spec summary, and test results.
2. **Audit independently:** Use a fresh subagent or adopt a strict independent reviewer pass. Never rationalize away gaps using implementer intent.
3. **Classify findings by severity:**
   * **Critical (Blocks progress):** Correctness bugs, security flaws, data loss risks, missing spec requirements, failing/weak tests.
   * **Important (Fix before merge):** Edge-case gaps, poor error handling, brittle coupling, maintainability debt.
   * **Minor (Optional polish):** Style nitpicks or minor naming tweaks.

---

## 11. Receiving Code Review (`receiving-code-review`)

Respond to human or automated review feedback with technical rigor, zero defensiveness, and zero blind compliance.

1. **Read completely before replying:** Understand the full feedback set first.
2. **Verify against codebase reality:** Check whether each claim is factually true in this codebase.
3. **Clarify ambiguity first:** If a comment is unclear or conflicts with another requirement, ask before editing.
4. **Push back with evidence when wrong:** If a suggestion breaks a requirement, introduces regressions, or violates YAGNI, explain why concisely with code/test evidence.
5. **Fix cleanly without performative praise:** Skip fluff ("Great catch!"). Apply valid fixes one by one, test each, and report what changed.

---

## 12. Verification Before Completion (`verification-before-completion`)

**Iron Law:** `NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.`

Before using words like *"fixed"*, *"done"*, *"passing"*, *"ready"*, or *"verified"*:
1. Identify the exact command(s) proving the claim (tests, linter, typechecker, build, reproduction script).
2. Execute the command **fresh** after your final edit (never rely on earlier runs or memory).
3. Read the **entire output**, exit code, and pass/fail counts.
4. Report the exact command run and observed result. If any check could not be run, state explicitly what remains unverified.

---

## 13. Finishing a Development Branch (`finishing-a-development-branch`)

Trigger only after **Section 12 (Verification)** passes cleanly with zero failing tests.

1. **Verify clean state:** Confirm all tests pass and check `git status` for stray or untracked files.
2. **Determine base branch:** Confirm target branch (e.g., `main` or `develop`) and check for merge conflicts.
3. **Present 4 explicit options to the user:**
   1. **Merge locally** into base branch and clean up branch/worktree.
   2. **Push & open Pull Request** (preserving branch/worktree until merged).
   3. **Keep branch/worktree as-is** for later work.
   4. **Discard branch/worktree** (require explicit typed confirmation before destructive cleanup).
4. **Execute chosen option** and verify post-action git state.

---

## 14. Workflow Self-Audit (`diagnosing-superpowers`)

Use when a session drifted, skipped a gate, looped on errors, or burned excessive tokens.

1. **Identify the failure mode:** Missed trigger, skipped TDD/verification, runaway subagent retries, context compaction loss, or over-engineering a trivial task.
2. **Trace the root cause:** Inspect the exact turn where discipline broke down and what rationalization caused it.
3. **Apply a targeted correction:** State the missed rule explicitly, rewind or re-verify the affected step, and adjust scope (e.g., switch from subagents to inline execution if token burn is too high).

---

## 15. Authoring New Skills (`writing-skills`)

Apply TDD to documentation whenever creating or refining a `SKILL.md` file.

1. **Validate format:**
   * YAML frontmatter with **only** `name` (lowercase letters, digits, hyphens; <= 64 chars) and `description` (third-person, starts with `"Use when..."`, lists triggers/symptoms only—never summarize workflow steps or agents will skip reading the body).
   * Keep `SKILL.md` concise (< 500 lines); place heavy scripts or docs in `references/`.
2. **RED (Baseline Test):** Run a realistic pressure scenario *without* the skill and document exact failure modes and excuses.
3. **GREEN (Minimal Skill):** Write the leanest rules needed to fix the observed failures.
4. **REFACTOR (Bulletproof):** Re-test under combined pressures (time pressure, sunk cost, ambiguity), add explicit counters to the rationalization table below, and tighten wording until behavior is consistent.

---

## Anti-Rationalization & Red Flags Table

If you catch yourself thinking any excuse on the left, **STOP** and follow the reality on the right.

| Agent Excuse / Red Flag | Operational Reality |
| :--- | :--- |
| "This change is too simple to need a test first." | Simple code breaks subtly. Write the failing test in 30 seconds. |
| "I'll write the tests right after I finish coding." | Tests written after code verify what you wrote, not what was required. Start from RED. |
| "I already know the cause—let me apply a quick fix." | Unverified guesses create whack-a-mole loops. Prove the root cause first. |
| "It should pass now / looks right to me." | "Should" is not evidence. Run the command and read the actual output. |
| "I ran the tests two edits ago and they passed." | Stale output proves nothing. Re-run after the final edit. |
| "Let me try one more tweak" (after 2 failed fixes) | Stop thrashing. Re-evaluate assumptions and consult the user. |
| "The user is in a hurry; skip brainstorming/planning." | Building the wrong thing fast is slower than clarifying first. |
| "I'll clean up unrelated files while I'm here." | Unrequested changes cause regressions and noisy diffs. Stay scoped to the plan. |