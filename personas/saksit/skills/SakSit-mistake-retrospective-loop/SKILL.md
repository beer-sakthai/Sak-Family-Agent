---
name: SakSit-mistake-retrospective-loop
category: core
description: Learn from mistakes and prevent recurrence.
version: 0.1.0
author: Hermes
platforms: [linux]
tags: [Retrospective, Learning, Improvement, Post-Mortem]
---

# Mistake → Lesson → Improvement

A structured post-mortem loop: when something goes wrong, capture the mistake,
extract the root cause, and save a permanent fix — not a bandaid. The goal is
that the same mistake never happens twice.

This is a **meta-skill**: it governs how you respond to failures, not how you
do the task itself. Use it after any broken config, wrong assumption, runaway
process, or user correction.

**Complement: proactive self-audit.** This skill is reactive — it fires *after*
a mistake. To close the full learning loop, pair it with a periodic proactive
self-audit that checks your actual behaviour against your stated standards
(trust ladder compliance, memory hygiene, skill loading, token economy,
verification discipline) *before* a mistake happens. The reactive loop catches
failures; the proactive audit catches drift. See LEARNING_JOURNAL.md entry
2026-07-25 (Assistant Excellence | Self-improvement & learning loops) for the
full pattern.

## When to Use

- User corrects you on something you should have known
- A config change breaks something unexpectedly
- A job, cron, or script ran but produced nothing useful
- A process kept running after it should have stopped
- User says "I asked for X, you did Y" (trust ladder violation)
- A fix you applied turned out to be premature or wrong-order
- Any repeating mistake pattern across sessions

## The Loop (4 Phases)

```
     ┌──────────────────────────────┐
     │  FAILURE / MISTAKE / ISSUE   │
     └──────────────┬───────────────┘
                    ▼
     ┌──────────────────────────────┐
     │  1. OBSERVE — What actually  │
     │     happened? What were the  │
     │     symptoms?                │
     └──────────────┬───────────────┘
                    ▼
     ┌──────────────────────────────┐
     │  2. ROOT CAUSE — Why did it  │
     │     happen? What system or   │
     │     decision enabled it?     │
     └──────────────┬───────────────┘
                    ▼
     ┌──────────────────────────────┐
     │  3. FIX — Apply the real     │
     │     correction, not a patch. │
     │     Verify it's green.       │
     └──────────────┬───────────────┘
                    ▼
     ┌──────────────────────────────┐
     │  4. SAVE — Persist the       │
     │     lesson as a skill,       │
     │     memory, or procedure     │
     └──────────────┬───────────────┘
                    │
                    ▼
              BACK TO WORK
```

### Phase 1: Observe

Before you try to fix anything, audit the current state:

- `cronjob(action='list')` — what's actually running vs what you think is running
- `read_file()` on configs, `search_files()` for stale entries
- Check output/log directories for evidence a job actually produced something
- Ask: "What did I build, and has it ever produced a result?"

**Key rule:** Count before stating. `ls | wc -l`, not "a bunch of files."
If you can't verify it with a command, don't claim it.

### Phase 2: Root Cause

Find the decision that enabled the failure — not the proximate trigger.
Ask "why" repeatedly:

| Level | Question | Example from this session |
|-------|----------|--------------------------|
| Symptom | What broke? | Selfheal had 13 runs, 0 useful work |
| Decision | What got it wrong? | I built selfheal before learning jobs ran |
| Rule | What principle was violated? | Defense before offense |
| Fix | What prevents recurrence? | Verify the primary system runs first, then add protective layers |

### Phase 3: Fix

Apply the correction with these priorities:

1. **Kill the wrong thing first** — stop the leaking pipe before designing the
   replacement. Remove the broken job, revert the bad config, undo the change.
   Use `cronjob(action='remove')` or `patch()` to revert.

2. **Fix the root cause, not the symptom.** The selfheal wasn't the problem —
   the ordering was (defense before offense). Removing the selfheal was the
   right fix because the learning system hadn't proven itself yet.

3. **Get the primary working before adding safety.** Default to offense-first:
   make the core function produce results, then add guards. Adding a watchdog
   before the watched system ever runs is wasted complexity.

4. **Verify green before reporting done.** The fix isn't real until you've
   confirmed with a tool call that state is correct.

### Phase 4: Save

Persist the lesson so future sessions can't repeat the mistake:

| If the lesson is about... | Save to... | Method |
|--------------------------|-----------|--------|
| A repeatable procedure | SKILL.md | `skill_manage(action='create')` |
| A user preference | memory (`target='user'`) | `memory(action='add', target='user')` |
| An environment constraint | memory (`target='memory'`) | `memory(action='add', target='memory')` |
| A mistake pattern to avoid | SKILL.md Pitfalls section | `skill_manage(action='patch')` on relevant skill |

**The 4-Part Post-Mortem format for each saved lesson:**

```
## [mistake-name]

- **What happened:** Brief description.
- **Root cause:** The decision/assumption that enabled it.
- **Fix applied:** What was done to correct it.
- **Prevention:** What skill/memory/rule prevents recurrence.
```

## Common Mistake Patterns (from real failures)

### Pattern A: Building before verifying
You add a safety system, watchdog, or fallback before the primary system
has ever produced output.

**Fix:** Verify the core function produces a result first. Then add layers.
Test in this order: Does it run? → Produces output? → Output is correct? →
Now add monitoring/guards.

### Pattern B: LLM-driven sync instead of script
A recurring sync task uses an agent prompt (LLM-driven, burns tokens) when
a no_agent script would do the same work for free.

**Fix:** For pure file-manipulation, data-sync, or stateless-check tasks, use
`no_agent=True` with a `script` path. Reserve LLM jobs for tasks that need
reasoning, deduction, or judgment.

### Pattern C: Premature scaling
You add 5 jobs, 4 tool integrations, or 3 cron topics before any of them
have proven they work individually.

**Fix:** Prove one thing end-to-end before shipping the next. One working
learning job is worth more than 5 scheduled but never-tested ones.

### Pattern D: Silent runaway
A job is scheduled with `enabled: true` and high repeat count, runs
silently, and the agent never checks whether it's still producing useful
work.

**Fix:** Recurring jobs that deliver `local` still need occasional
verification. Use the `garda-audit-weekly` pattern: a periodic check that
confirms each job has run recently and produced output.

### Pattern E: Config mutation without confirmation
Changing profile config, environment variables, or credentials without
explicit user approval.

**Fix:** Climb the trust ladder: Read → Suggest → Draft → Confirm → Act.
Always `read_file` before `write_file` on config files. Never `hermes config
set` without proposing the specific change first.

## Procedure

When you catch yourself about to start a fix, run this checklist first:

1. **`cronjob(action='list')`** — What's actually running right now?
2. **Check outputs** — Do the existing jobs produce anything real?
3. **Pick ONE thing to fix** — Not three. Not "all of them." One.
4. **Confirm the fix with user** — "I see X issue. Proposed fix: Y. Good?"
5. **Apply** — One change at a time.
6. **Verify** — Did it actually work? Run the job or check state.
7. **Save lesson** — What pattern does this belong to? Save to relevant skill.

## Pitfalls

- **Confusing "output" with "value."** A job can run and produce output that's
  empty, stale, or noise. Check content, not just exit codes.
- **Over-relying on the selfheal.** A watchdog only catches state changes in
  jobs.json. It cannot detect: a job that runs but produces worthless output,
  a job that errors silently, or a job that never fired because the scheduler
  skipped it. Selfheal is a last resort, not a primary strategy.
- **Fixing symptoms, not systems.** "The selfheal ran 13 times" is a symptom.
  "I built defenses before offense" is the root cause. Fix the ordering, not
  the tool.
- **Saving to memory but not a skill.** Memory is per-session context and
  expires or gets replaced. Reusable procedures must be saved as skills
  (`skill_manage`) or they vanish on next session.

## Verification

After completing the 4-phase loop, confirm:

```
1. The mistake is no longer happening (check cron state / config / etc.)
2. A skill, memory, or procedure now exists that prevents recurrence
3. You can point to the specific prevention and explain why it works
```
