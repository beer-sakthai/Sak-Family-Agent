---
name: execution-discipline
description: >
  Class-level execution discipline for bounded, evidence-first action.
  Apply whenever the next step is uncertain, a fix is unconfirmed, or the
  user explicitly asks the agent to stop guessing. Governs the boundary
  between reasoning and execution: if no clear cure is supported by real
  evidence, the agent must state that, summarize what is known, and offer
  the next verification step instead of acting.
triggers:
  - insufficient evidence
  - unclear failure cause
  - stop vs act decision
  - speculative execution
  - no clear cure
  - user says don't guess
  - unresolved tooling mismatch
  - avoid guessing
---

# Execution Discipline

This skill enforces the execution boundary between **reasoning** and
**acting**. It exists because guessing is not free: it consumes turns,
pollutes context, and can produce misleading “fixes” that harden into
false constraints.

## Principle

**If no clear cure is supported by real evidence, say so and stop.**
Action is only justified when at least one actionable hypothesis is
grounded in authoritative evidence.

## When this applies

- A tool/network/environment failure has no clear cause from the
  current diagnostic data.
- Known facts are conflicting or incomplete.
- A proposed fix relies on analogy or pattern-matching rather than
  explicitly authoritative sources (docs, reproducible artifacts,
  direct inspection).
- The user explicitly asks the agent to stop guessing.
- A workspace has known unresolved mismatches (for example,
  `pip` pointing to a different Python than the editor/lint chain).

## Required behavior

1. **State the boundary.**
   Say plainly whether the current evidence is sufficient to act.
2. **Summarize knowns and missing pieces.**
   One or two bullets each. Keep it tight.
3. **Propose a single verification step.**
   The smallest action that would resolve the ambiguity, if the user
   wants it.
4. **Do not execute speculative commands.**
   Especially avoid retry loops, blind `pip install` attempts, or
   publishing proposed fixes with unverified causes.

## Expected output shape

> What failed / why it is unclear / what is missing / one concrete
> next check if the user wants to continue.

## Pitfalls

- “Let’s just try X” without a hypothesis tied to evidence.
- Re-running the same probe hoping for a different result.
- Publishing a fix plan that names causes you cannot confirm.
- Continuing to act after stating you do not know.
- Acting on an environment state you have not verified in this session.

## Relation to reasoning and debugging skills

This skill is the execution boundary for reasoning frameworks such as
`nine-step-reasoning` and debugging workflows like
`systematic-debugging`. Those skills define how to analyze; this skill
defines when not to act.

## Session evidence

For real cases from this session, see `references/execution-patterns.md`.
