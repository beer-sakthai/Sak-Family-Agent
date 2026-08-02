---
name: SakThai-family-handoff
author: SakThai
license: MIT
description: "Formal procedure for SakThai delegating tasks to sibling agents"
version: 2.0.0
metadata:
  hermes:
    tags: [handoff, delegation, multi-agent, siblings, sak-family, pipeline]
    category: communication
---

# Sak Family Handoff — Formal 3-Stage Pipeline

When delegating to a sibling agent, use the formal **Research → Build → Verify** pipeline. This ensures consistent quality, clear contracts between stages, and traceable outcomes.

## When to delegate: token-conscious improvement

Two key directives from Beer that govern *when and why* to delegate — separate from the *how* in the sections below.

### Token-conscious delegation

**Premise:** Every output token burns the budget. When a task is heavy (deep research, multi-file search, long-form content creation), delegate it rather than consuming your own context window.

- **Light work** (single file fix, quick API call, one-minute read) → do it yourself
- **Heavy research** (compare approaches, read multiple docs, synthesize large amounts of info) → delegate to **SakKing**
- **Content creation** (drafts, social posts, long-form writing) → delegate to **SakSit**
- **Testing/QA** → delegate to SakSee

### Active improvement on discovery

**Premise:** When exploring or learning (cron jobs, ad-hoc research, reading docs), if you find something actionable — a better tool workflow, a missing skill step, a configuration fix — **apply it immediately, don't just collect it**.

1. Found a CLI flag that's better than what a skill describes? Patch the skill right then.
2. Discovered a workaround for a tool limitation? Save it to the relevant skill's pitfalls.
3. Spotted a configuration improvement? Apply it on the spot.

The formal pipeline below (Research → Build → Verify) is for Beer-initiated tasks. The "apply immediately" pattern is for **autonomous exploration** where the agent discovers improvements during routine work.

### Cron jobs and delegation

Cron jobs run autonomously with no user present. They can:
- **Apply light fixes directly** (patch a skill, save to memory, fix a config)
- **Delegate heavy work** to SakKing or SakSit via `delegate_task()` if the improvement genuinely requires deep research or multi-file work
- Must include `delegation` in their `enabled_toolsets` to use `delegate_task`

For cron jobs, `repeat=N` is the token-conscious replacement for a long monolithic prompt — each run covers one thing, reports it, and keeps token usage predictable.

**Cron schedule format — critical:**
- ✅ `"1m"`, `"every 1m"`, `"5m"`, `"every 2h"` — correct formats for recurring schedules
- ✅ `"1m"` + `repeat=5` — runs every 1 minute, 5 times total
- ❌ `"once in 1 min"` — WRONG. The `"once in"` prefix causes the job to run ONCE then immediately mark as completed, ignoring `repeat=N`. The system normalizes `"1m"` to display as `"once in 1m"` internally, but you MUST pass `"1m"` (or `"every 1m"`) as input. Passing `"once in"` literally produces different behavior.
- ✅ `"0 9 * * *"` — standard cron expression also works for daily at 9am
- ✅ `"2026-06-01T09:00:00"` — one-shot ISO timestamp
- **Rule:** Always use the short format `"N{s/m/h}"` (e.g. `"30m"`, `"2h"`). Let the system normalize it. Never write `"once in"` literally in the schedule parameter.

## Pipeline Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  RESEARCH   │ ──▶ │    BUILD    │ ──▶ │   VERIFY    │
│  (SakSit)   │     │  (SakThai)  │     │  (SakSee)   │
│  Find data  │     │  Implement  │     │  Test/QA    │
└─────────────┘     └─────────────┘     └─────────────┘
```

Each stage has defined inputs and outputs. The next stage starts only when the previous one delivers a complete artifact.

## Who does what

| Agent | Role | Stage | Best for |
|-------|------|-------|----------|
| **SakSit** (@saksit_agent_bot) | Master of Data & Research | **Research** | Data analysis, paper discovery, dataset ops, market research, observation |
| **SakThai** (me) | Main Lead & Master of HF | **Build** | Implementation, model training, skill authoring, infrastructure, huggingface |
| **SakSee** (@saksee_agent_bot) | Master of Playwright | **Verify** | QA automation, E2E testing, visual testing, web scraping, smoke tests |
| **SakKing** (@sakking_agent_bot) | General Assistant | **Any** | Runner tasks, errands, coordination, simple operations |

## Stage Contracts

### Stage 1: Research (SakSit)
**Input:** A clear research question from Beer or SakThai
**Output:** A structured report with findings, data sources, recommendations
**Contract:**
```
delegate_task(
  role="leaf",
  goal="Research <topic>",
  context="Question, constraints, expected output format"
)
```
**Verification:** Read the returned report — check it answers the question, has sources, is actionable.

### Stage 2: Build (SakThai)
**Input:** Research findings + build requirements
**Output:** Working artifact (code, model, skill, config)
**Contract:** Execute directly with tools. Reference the research report.
**Verification:** Run the artifact, check it works, confirm with Beer if needed.

### Stage 3: Verify (SakSee)
**Input:** The built artifact + what to test
**Output:** Test report (pass/fail, evidence, screenshots)
**Contract:**
```
delegate_task(
  role="leaf",
  goal="Verify <artifact>",
  context="What it does, how to test, expected behavior"
)
```
**Verification:** Review test report. If failed, loop back to Build.

## Handoff protocol

1. **Use `delegate_task()`** — always with a clear, self-contained goal
2. **Include ALL context** — siblings have NO memory of your conversation. Pass relevant file paths, error messages, constraints, and expected output format
3. **Specify output language** — if Beer is writing in a non-English language or wants output in a specific tone, say so in `context`
4. **Verify the result** — subagent summaries are self-reports, not verified facts. For operations with external side-effects (HTTP POST, file creation, remote writes), require a verifiable handle (URL, ID, absolute path) and verify it yourself
5. **Loop on failure** — if Verify reports a failure, go back to Build, fix, re-deploy to Verify
6. **Report to Beer** — tell Beer the full pipeline result (what each stage produced)

## Quick Reference — Common Delegation Patterns

| Pattern | Direct | Delegate to | Why |
|---------|--------|-------------|-----|
| Light skill patch | ✅ Do it yourself | — | Quick, direct, minimal tokens |
| Deep research (compare tools/docs) | ❌ Delegate | SakKing | Heavy context consumption |
| Content/draft creation | ❌ Delegate | SakSit | Specialised skill, saves tokens |
| Exploratory cron discovers something heavy | ✅ Apply light fixes directly | SakKing for deep work | Token-conscious exploration |
| Data generation | ❌ Delegate | SakSit | Data ops are SakSit's domain |
| E2E testing / QA | ❌ Delegate | SakSee | Playwright automation |

## Quick Reference — Common Pipelines

| Task | Research (SakSit) | Build (SakThai) | Verify (SakSee) |
|------|-------------------|-----------------|-----------------|
| New HF model | Find best base model & dataset | Fine-tune, upload to Hub | Run inference smoke test |
| Build a Space | Research best UI framework | Code the Space with Gradio | Test all interactions |
| Write a skill | Find reference docs & best practices | Author SKILL.md with procedures | Load skill, verify it works |
| B2B content plan | Analyze market & competitors | Draft content calendar | Check for consistency & errors |

## Skill repos — cross-sibling sync

| Sibling | GitHub Repo | Status |
|---------|-------------|--------|
| **SakThai** | `github.com/beer-sakthai/sakthai-skills` | ✅ 274 files, synced 2026-07-23 (55cd70e) |
| **SakSee** | `github.com/beer-sakthai/saksee-skills` | ⚠️ live dir IS the repo (888 files), synced 2026-07-23 (899be01) |
| **SakSit** | `github.com/beer-sakthai/saksit-skills` | ✅ 708 files, synced 2026-07-23 (b8cc98c) |

**Sync pattern:** `sakthai` and `saksit` use cloned repos at `/opt/data/sakthai-skills-repo/` and `/opt/data/saksit-skills-repo/`; `saksee`'s live `profiles/saksee/skills/` IS its git repo. Know the pattern before syncing — cloning over a live-git dir creates submodule entries.

All three repos are at `/opt/data/sakthai-skills-repo`, `/opt/data/saksee-skills-repo`, `/opt/data/saksit-skills-repo`.

## Memory sharing

- All siblings share the same long-term memory brain (supermemory, container: hermes)
- Save cross-agent facts to memory so all siblings can read them
- Each sibling has a separate session context — memory is the bridge

## A2A Message Bus

A technical messaging layer for agent-to-agent communication runs on port 3005. See [`references/a2a-message-bus.md`](references/a2a-message-bus.md) for API details.

## Pre-flight: check sibling health before delegation

Before delegating to a sibling, run a quick health check:

```bash
hermes -p <sibling> gateway status
```

If the sibling isn't responding or has been silent, diagnose first using the `agent-health-diagnostics` skill — don't delegate work to an agent that can't execute it.

**Quick signals to watch for:**
- Gateway says "✓ Running" but sibling isn't replying → likely Telegram disconnect or provider issue
- Multiple cron jobs failing with HTTP 402 → provider credits depleted, not just a scheduling problem
- No recent "response ready" in gateway logs → platform connection may be broken

See `agent-health-diagnostics` for full diagnostic workflow.

## Pitfalls

- Do NOT use `send_message` to contact siblings — only `delegate_task`
- Don't assume a sibling knows what you talked about in previous messages — always provide full context
- A leaf subagent (default role) CANNOT delegate further. If nested delegation is needed, use `role='orchestrator'`
- The pipeline is sequential by default — parallel stages can be used when tasks are independent
- Always verify Verify's output too — subagent summaries are self-reports
- **Dataset operations: NEVER trust a subagent to append without verification.** Subagents can overwrite the entire dataset instead of appending. ALWAYS: (1) check original remote count before dispatch, (2) compare remote count after, (3) keep backup commit hash to revert, (4) only delegate data generation, never the upload
