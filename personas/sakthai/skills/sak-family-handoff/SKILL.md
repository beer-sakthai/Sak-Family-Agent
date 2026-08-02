---
name: sak-family-handoff
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

## Pitfalls

- Do NOT use `send_message` to contact siblings — only `delegate_task`
- Don't assume a sibling knows what you talked about in previous messages — always provide full context
- A leaf subagent (default role) CANNOT delegate further. If nested delegation is needed, use `role='orchestrator'`
- The pipeline is sequential by default — parallel stages can be used when tasks are independent
- Always verify Verify's output too — subagent summaries are self-reports
