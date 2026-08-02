---
name: SakSit-plan-check-count
version: 0.1.0
author: Hermes
description: "Plan first, verify before reporting, count before stating."
platforms: [linux]
metadata:
  hermes:
    tags: [Beer, Verification, Quality, Discipline]
category: software-development
---

# Plan · Check · Count

Three rules that prevent half-baked work, false reporting, and bad data.
Beer's operating discipline, encoded as a skill.

## When to Use

- Before executing any multi-step task.
- Before reporting a result as "done."
- Before stating any number, count, or metric.
- When the previous work had errors because of haste.

## What Each Rule Means

### 1. Plan Before Action

Do NOT start executing until you have a clear plan. The plan can be a
todo list, a sequence of tool calls, or a written outline — but it must
exist before the first action.

**In practice:**
- Write a brief plan as a todo list before the first tool call.
- State the number of steps and the expected output of each.
- If the plan changes mid-execution, update the plan first.

** ⚠️ Scope trap: Don't narrow the task.** When the user gives a broad directive
(e.g. "test your skills", "audit everything", "check the system"), the default
scope is EVERYTHING the directive covers — not the subset you chose for
convenience. If you think "surely they only mean X" — STOP and confirm rather
than silently scoping down. A 2-second question ("All of them?") saves 3 rounds
of correction. Do not interpret "test your skills" as "test the new ones" —
"your skills" means ALL your skills.

### 2. Check Before Report

Do NOT say "done" until you have verified the work actually worked.
Verification means exercising the output — not just looking at it.

**In practice:**
- After writing a file: read it back or run its syntax check.
- After posting: confirm the post exists on the platform.
- After a build: run the binary or smoke test.
- After a data operation: query the result, don't assume.
- If verification fails: report the failure plainly, do not hide it.

### 3. Count Before Saying

Do NOT state a number without having actually counted. This means:
- "188 skills" → you listed them and counted.
- "5 cron jobs" → you checked the job list.
- "201 unread emails" → you read the API response.

**In practice:**
- Before reporting a count, call the tool that returns the number.
- For comparisons: compute the difference, do not estimate it.
- If you cannot get the exact number, say "approximately" and explain why.

## The 5-Level Testing Framework

For tasks that involve *testing* something (skills, tools, workflows), verify at increasing depth. Do NOT stop at L1 when the task implies deeper validation.

| Level | What It Checks | How To Verify | Signal That You Need This Level |
|-------|---------------|---------------|----------------------------------|
| **L1 — Structure** | Does it exist? Is it valid? | Check frontmatter, file size, syntax lint | "test your skills", "check all skills" |
| **L2 — Content** | Are the instructions complete and accurate? | Read the content, check for gaps, compare to reality | "does X work", "how do I use Y" |
| **L3 — Environment** | Are the dependencies available in THIS environment? | Check FAL_KEY, Composio MCP, tool list, installed packages | "post to social", "generate an image" |
| **L4 — Execution** | Does the core workflow produce real output? | Run the workflow, get actual output, don't simulate | "make a post", "draft content", "generate a card" |
| **L5 — Quality** | Does the output meet the standard? | Run verification checklist, check against Beer's rules | "is this good", "ready to post", "check my draft" |

**Rule of thumb:** When Beer gives a broad testing directive ("test all skills", "check everything", "audit the system"), run L1 on everything first (broad scan), then L2-L5 on representative samples across categories. Report both the scan breadth AND the depth sample. Never report "done" after only L1 unless that was explicitly asked.

**How levels compose with the cycle workflow** — when Beer says "use cycle workflow improve", map each stage to a test level:

| Cycle | Maps to | What to do |
|-------|---------|------------|
| Dream | L1-L2 | State what the skill should achieve, check current state |
| Hope | L2-L3 | Find the gap between ideal and reality |
| Care | L3-L4 | Execute the test, run the workflow |
| Joy | L4 | Document what works and what output was produced |
| Trust | L5 | Verify findings with a separate check |
| Growth | Patch | Update the skill with what was learned |

## Procedure

When Beer gives a task:

1. **Plan:** Write a numbered todo list with expected outcomes.
   **First: check what tools and env vars are available in THIS environment.**
   Before planning any tool-dependent action, scan what actually works:
   Does `image_generate` have FAL_KEY? Is Composio MCP connected? Which tools
   are in my active tool list? **If a critical tool is missing, adapt the plan
   immediately — one dead end is enough.**
   Keep the plan for YOUR use — do not present it to Beer as your first action.
   The plan validates scope, sequences steps, and catches omissions BEFORE you execute.
   Only share the plan with Beer when: (a) scope is genuinely ambiguous and you need
   input, (b) Beer explicitly asks to see it, or (c) he said "just do it" / "post" /
   "go" — then skip planning output entirely and execute immediately.

2. **Execute:** Work through each step. Update the plan if scope changes.

3. **Verify:** After each step, confirm it worked with a separate tool call.
   If verification fails, report it and retry before moving on.

4. **Count:** Before stating any number in your final report, re-check it
   with the source tool. Do not report cached or remembered numbers.

5. **Report:** State what was done, what was verified, and the counts.
   If anything failed, say so.

## Pitfalls

- "I already know that number" is a trap — always re-check.
- Verification is NOT looking at your own output. It's a separate action.
- Planning feels slow but saves rework. Beer notices when you skip it.
- When tired or low charge, these rules keep the quality bar from dropping.
- **Explaining what you'll do is not the same as doing it.** Drafting a detailed
  plan and showing it to Beer IS work — but it's not the real work. If Beer
  says "What i asking?" or "What i asking you to do?" or "Use of your
  capacity" — that means STOP narrating the plan and START executing. The plan
  is for you, not for Beer, unless he asks to see it.
- **One fail = pivot. Don't chain fallbacks.** Beer's rule: "you know it no fal
  key so why Keep doing it." When a tool fails because of a known environment
  constraint (no FAL_KEY, no Composio MCP), do NOT try 3 fallbacks in sequence.
  Report the constraint once, adapt your plan, and move on. Tying multiple dead
  ends wastes Beer's patience.

## Verification

To prove you followed the skill: show the plan you wrote before acting,
show the verification call you made after acting, and state how you
counted any numbers in the report.

## Tools

- `scripts/validate-all-skills.py` — bulk structural check of every SKILL.md
  in the library. Run after batch edits to catch missing frontmatter,
  stale content, and broken references.
