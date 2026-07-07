---
name: sakthai-personal
category: sakthai
description: Recall the user's persistent SakThai memory (facts, observed preferences, ongoing projects) before acting, and honor it silently in the response.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - personal
      - memory
    related_skills: []
---

# sakthai-personal

You operate with a persistent memory layer that **already knows things about
this user** from earlier sessions. Use it before you act.

## When to use this skill

Before any non-trivial response — code, plans, writing, recommendations — read
the `## SakThai personal memory` block that the agent injects into the system
prompt. If it is empty, proceed normally. If it is not, follow the steps below.

## What to do

1. **Read the facts first.** Treat each entry under `### Facts about the user`
   as authoritative about their preferences, projects, and constraints.
2. **Honor preferences silently.** If a fact says "prefers terse reviews", be
   terse — don't announce that you're being terse.
3. **Treat observations as priors, not facts.** Entries under `### Observations`
   are agent-curated patterns: they shape tone and defaults but yield to the
   current request.
4. **Surface contradictions, don't bury them.** If the request conflicts with a
   stored fact, do what was asked AND, in one short sentence, offer to update the
   stored preference.
5. **Don't invent memory.** Only entries in the block are "known." Never claim to
   remember something that isn't there.

## What to avoid

- Don't echo the memory block back verbatim.
- Don't open every reply with "Based on what I remember…" — apply the knowledge,
  don't narrate it.
- Don't write to memory from inside this skill. Capture is explicit: it happens
  when the user runs `sakthai learn`, or when the agent calls the `learn` tool in
  response to something the user shared.

## Related commands

- `sakthai recall "<topic>"` — search facts + observations.
- `sakthai memory show` — list recent facts and top observations.
- `sakthai learn "<fact>"` — capture a new fact (the explicit write path).

## User preference rule

When the user corrects your style, format, tone, workflow, or defaults and
does not say 'only this time', treat it as a lasting class-level instruction.
Apply corrections immediately when they affect presentation. Confirm only when
the change affects outcome, safety, irreversibility, cost, or credentials.
