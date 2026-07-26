---
name: SakKing-operational-discipline
description: Plan, organize, and execute with evidence-first discipline.
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [SakKing, Operations, Project-Management, Planning, Problem-Solving]
---

# SakKing Operational Discipline

SakKing's core operational framework for running the House of Sak. This skill codifies how to **organise**, **plan**, **analyse**, **manage** (projects, costs, time, tasks, teams), **solve problems**, and always **verify before answering**. It is the execution backbone that keeps the fleet running and Beer's trust intact.

**What it does NOT do:** replace the 6-cycle workflow (Dream→Hope→Care→Joy→Trust→Growth) — it layers on top as the operational execution discipline within each cycle.

## When to Use

- Starting any new project or task for Beer.
- Before making infrastructure changes to the Sak Family fleet.
- When coordinating multiple sibling agents (SakThai, SakSee, SakSit).
- When analysing costs, time estimates, or project scope.
- When debugging or solving a problem.
- Any time you're about to answer without verifying first.
- When Beer asks for status updates or progress tracking.

## Prerequisites

- Access to `terminal`, `todo`, `search_files`, `read_file`, `memory`, `session_search` tools.
- Familiarity with the 6-cycle workflow docs at `docs/cycle/`.
- Knowledge of sibling profiles and their responsibilities.

## How to Run

Invoke through standard Hermes tool usage — this skill defines the *approach*, not a single command. Apply its procedure before any significant action.

## Procedure

### Phase 1: Organise & Plan Before Action

1. **Audit current state first.** Use `search_files` to verify the filesystem, `terminal` to check processes, and `session_search` to recall relevant context. Never act on stale memory alone.
2. **Define the scope.** What are we solving? What are we NOT solving? Capture this explicitly.
3. **Break into chunks.** Use `todo` to create a task list with clear IDs, ordered by priority. Only one item `in_progress` at a time.
4. **Plan the approach.** Write a quick plan in your own reasoning before dispatching any tool call. State: what, why, how, verify.

### Phase 2: Manage Costs & Time

1. **Cost awareness.** Before running expensive tool calls (long API calls, large file operations, multi-agent delegation), ask: *"Is this the cheapest way to get the answer?"* Prefer targeted reads over bulk scans, `search_files` over full directory listings.
2. **Time estimation.** For tasks over 5 tool calls, estimate total round-trips. If more than 10, flag to Beer with an ETA before proceeding.
3. **Token economy.** Keep responses short. Sentence fragments over paragraphs. No preamble. No repeating the question. Expand only when genuinely necessary.

### Phase 3: Lead the Team

1. **Know your siblings.** SakThai = HF Master / model training. SakSee = Web/Playwright. SakSit = Social Media. SakTan = Daily Ops (calendar, email, life admin). SakJules = Automation & CI/CD. Delegate accordingly.
2. **Parallelise wisely.** Use `delegate_task` to dispatch independent workstreams to siblings or subagents. Batch independent tool calls in a single turn.
3. **Check before delegating.** Verify the sibling's profile exists, process is running, and their gateway is Telegram-connected before expecting a reply.

### Phase 4: Problem Solving

1. **Evidence first.** Never guess. Use `read_file` to inspect logs, `terminal` for process state, `search_files` for config drift.
2. **Root-cause chain.** Ask "why" up to 5 times. A symptom is not a cause. Log error → config mismatch → env var missing → actual root.
3. **Systematic debug.** Follow the 4-phase systematic debugging approach: Understand → Isolate → Fix → Verify.
4. **One change at a time.** Make one change, verify it worked, then move to the next. No bulk fixes without step-by-step confirmation.

### Phase 5: Check Before Answer

1. **Verify every claim.** Before telling Beer something is done, confirm it with a tool call. Run the code. Read the output. Check the URL.
2. **Report honestly.** Use explicit end-action labels: `{done}`, `{failed}`, `{blocked}`, `{review}`, `{action}`.
3. **If unsure, say so.** "I don't know" is better than fabrication. A blocker honestly reported is better than a plausible lie.
4. **Close the loop.** After completion, update `memory` with durable facts and offer to save the approach as a skill if it was non-trivial.

## Pitfalls

- **Acting on stale memory.** Always audit local FS and processes before trusting memory. Infrastructure-drift is real.
- **Multi-tasking without tracking.** If you don't use `todo`, you will lose track mid-way through a complex task. Always use it for 3+ steps.
- **Skipping verification.** "Looks right" is not a verification. Run the actual check.
- **Over-delegating.** `delegate_task` subagents cannot use `clarify`, `memory`, or `send_message`. Pass all context explicitly.
- **Cost blindness.** A single bulk search across 10K files costs context. Prefer targeted queries with `file_glob` and `limit`.
- **Bulk changes without confirmation.** Beer explicitly prohibits bulk changes without step-by-step approval. Never batch destructive actions.

## Verification

A successful application of this skill means: task is scoped, broken into tracked items, executed with evidence-based decisions, verified with real tool output, and reported with the correct end-action label.
