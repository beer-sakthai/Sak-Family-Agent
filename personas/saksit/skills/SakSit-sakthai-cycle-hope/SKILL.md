---
name: SakSit-sakthai-cycle-hope
tags: [workflow, hope, cycle, sak-family]
category: core
description: Turn the Dream vision into a concrete, defensible plan (PTCF).
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - cycle
      - hope
    related_skills:
      - SakSit-sakthai-cycle-care

---

# sakthai-cycle-hope

Stage 2 of 6 in the Sak Family cycle — **Hope**. See [Hope.md](../../../../docs/cycle/Hope.md)
for the full guidance and [SOUL.md](../../../../docs/SOUL.md) for the charge model.

## What to do

Translate the vision into a plan: Problem, Technique, Considerations, Feedback. Capture each key decision with `sakthai learn --kind note --tag decision`. A good plan is disprovable enough for Care to audit.

**For content/promotion work (SakSit domain):**
- Break the vision into concrete deliverables (model cards, blog posts, social posts, demos, notebooks)
- For each deliverable: PTCF (Problem → Technique → Considerations → Feedback)
- Order by dependency (what blocks what) and effort (quick wins first)
- Check platform constraints upfront: karma requirements, token permissions, API availability, rate limits
- Default to parallel execution where deliverables are independent
- Always verify zero-cost viability — flag any paid service immediately

## Then

Advance with `sakthai cycle next` to move to the next stage (care).

**Hermes env fallback:** When `sakthai` CLI is unavailable, use `todo` tool to
track cycle stage progress.
