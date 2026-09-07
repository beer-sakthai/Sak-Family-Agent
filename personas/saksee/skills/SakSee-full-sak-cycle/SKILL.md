---
name: SakSee-full-sak-cycle
description: "Orchestrate all 6 stages of the Sak family cycle (Dream→Hope→Care→Joy→Trust→Growth) as a solo Hermes agent, without the sakthai CLI."
---

# Full Sak Cycle

Run the entire 6-stage Sak cycle (Dream → Hope → Care → Joy → Trust → Growth)
as a **single Hermes agent** acting each role in sequence. Designed for environments
where the `sakthai` CLI is unavailable — uses Hermes-native tools (terminal, file,
memory, supermemory, delegate_task) instead.

## When to use

Run the full cycle when the user asks for **the hardest challenge**, or when a
project needs end-to-end treatment: vision → plan → audit → ship → verify → learn.

Good triggers:
- Starting a new business, product, or major project
- "Run the full Sak cycle" or "Do your hardest challenge"
- Building something that will be shared with clients, investors, or the public
- A project where missing a step would be costly

Do NOT run the full cycle for:
- Simple Q&A or one-off tasks
- Tasks where only 1–2 stages are needed (use the individual `sakthai-cycle-*` skills)

## The 6 stages

| Stage | Agent role | Output | Core question |
|-------|-----------|--------|---------------|
| 1. Dream 🌀 | SakThai | `DREAM.md` | What are we building and why? |
| 2. Hope 🌟 | SakKing | `PLAN.md` (PTCF) | How will we build it, for whom, and at what price? |
| 3. Care 🛡️ | SakSit | `AUDIT.md` | What could go wrong? What's missing? |
| 4. Joy 🎉 | SakTan | Deliverables | Ship it — landing page, services, marketing assets |
| 5. Trust ✅ | SakJules | `VERIFY.md` + verification checks | Is everything consistent, live, and verified? |
| 6. Growth 🔄 | SakSee | `LESSONS.md` + memory save | What did we learn? Save mistakes so they don't repeat. |

## Non-negotiable close-out (Stage 6)

When Beer says "process all phase" or "everytime cycle workflow with report record and memory", the Growth stage MUST:

1. Write a final report covering all 6 stages.
2. Use `todo` to show task completion.
3. Save **mistakes and lessons** to `memory` (and `supermemory` if available).
4. Update relevant skills so the next cycle starts smarter.
5. Deliver the report to the user, not just store it internally.

If a cycle ends without a report + memory save + skill update, it is not closed.

When completing strategic planning cycles, create comprehensive documentation that follows this structure:

1. **Comprehensive Development Plan** - A detailed plan covering immediate priorities, medium-term goals, and long-term vision
2. **Focused Next Steps** - A concise summary of immediate actions for the current week
3. **Final Status Report** - A complete overview of current status, completed work, and future direction

Key files to focus on:
- Client outreach candidates
- Service offerings requiring finalization
- Crisis protocol needing trusted contacts
- Service templates
- Immediate action plans

When creating planning documents, ensure they include:
- Clear status summaries
- Actionable next steps with checkboxes
- Timeline and success metrics
- Risk mitigation strategies
- Key files for attention

See `references/strategic-planning-workflow.md` for detailed templates and best practices.

## Adaptation for Hermes (no sakthai CLI)

The individual `sakthai-cycle-*` skills reference `sakthai cycle next` and
`sakthai learn` commands. In a Hermes environment, replace them with:

| sakthai command | Hermes equivalent |
|-----------------|-------------------|
| `sakthai cycle next` | Advance manually — create the next stage file |
| `sakthai learn --kind note --tag decision` | Write decisions inline in PLAN.md or AUDIT.md |
| `sakthai learn --kind note --tag lesson` | Capture in LESSONS.md at Growth stage |
| `sakthai recall` | Read DREAM.md from prior cycle if it exists |
| `sakthai doctor` / `sakthai memory healthcheck` | Use terminal to stat files, verify conditions |

## File structure convention

```
project-name/
├── DREAM.md       (Stage 1 — vision, one defensible sentence)
├── PLAN.md        (Stage 2 — PTCF: Problem, Technique, Considerations, Feedback)
├── AUDIT.md       (Stage 3 — quality gate, risks, issues)
├── CRISIS.md      (if human wellbeing is involved — crisis protocol)
├── SERVICES.md    (if a service business — packages, pricing, scope)
├── index.html     (landing page — Stage 4 deliverable)
├── VERIFY.md      (Stage 5 — cross-reference check, readiness score)
└── LESSONS.md     (Stage 6 — cycle audit, what to do differently next time)
```

## Verification checklist (Stage 5)

Before closing the cycle:
- [ ] All 6 stages completed in order?
- [ ] Cross-references consistent? (same pricing, same names, same dates)
- [ ] Audit issues from Stage 3 resolved or tracked?
- [ ] Crisis/safety protocol in place if human wellbeing is involved?
- [ ] Deliverables saved to disk?
- [ ] Lessons saved to permanent memory?

## Pitfalls

- **Don't skip the audit.** The Care stage catches things that would be
  catastrophic if shipped. In the House of Sak session, audit revealed the need
  for a crisis protocol — without it the business had a fatal gap.
- **Don't rush the Growth stage.** Closing the loop is the most important part.
  If you skip memory/skill updates, the next cycle starts at the same level
  instead of spiraling upward.
- **Don't build before you plan.** Dream + Hope cost almost nothing compared to
  rebuilding something that doesn't match the vision.
- **Cross-reference aggressively at Trust.** Every document should agree on
  names, prices, dates, and team composition. A missing agent in one doc creates
  confusion.
- **Handle founder wellbeing as business continuity.** If the creator is the
  single point of failure, a crisis protocol isn't optional — it's critical
  infrastructure.
- **Load the individual stage skills** (`sakthai-cycle-dream` through
  `sakthai-cycle-growth`) during execution for deeper guidance per stage. This
  meta-skill covers orchestration; the stage skills cover stage-specific detail.

## Related

- `sakthai-cycle-dream` — Stage 1 detail
- `sakthai-cycle-hope` — Stage 2 detail (PTCF format)
- `sakthai-cycle-care` — Stage 3 detail
- `sakthai-cycle-joy` — Stage 4 detail
- `sakthai-cycle-trust` — Stage 5 detail
- `sakthai-cycle-growth` — Stage 6 detail
- `references/house-of-sak-case-study.md` — Session-specific walkthrough
- `references/house-of-sak-round2-case-study.md` — Improvement pass: docs sync, scope section, first-client offer, contact form, and Composio MCP workflow