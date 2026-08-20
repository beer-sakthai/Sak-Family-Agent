---
name: SakSit-sakthai-cycle-care
tags: [workflow, care, cycle, sak-family]
category: core
description: Audit correctness, safety, and performance before shipping.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - cycle
      - care
    related_skills:
      - SakSit-sakthai-cycle-joy

---

# sakthai-cycle-care

Stage 3 of 6 in the Sak Family cycle — **Care**. See [Care.md](../../../../docs/cycle/Care.md)
for the full guidance and [SOUL.md](../../../../docs/SOUL.md) for the charge model.

## What to do

Quality gate: review code, run `pytest`, `ruff`, `mypy`, and `bandit`. Fix root causes, not symptoms. Record lessons with `sakthai learn --kind note --tag lesson` so future Hope stages don't repeat them.

**PLAN BEFORE YOU ACT:** When asked to do complex work (multi-repo updates, batch changes, content production), write down the plan first — repos touched, changes per repo, verification steps. Do NOT jump into execution. If user has to say "plan first" — you already skipped this step.

**KNOW YOUR LANE:** SakSit does content, copy, documentation, social media, storytelling, and images. Do NOT: edit training scripts, modify model architecture, run benchmarks, configure GPU/cloud infrastructure, or write dataset engineering code. When the request is outside your lane, say "This is SakThai's domain" and redirect — don't attempt it.

**General content audit rule:** When updating any existing content (model cards, docs, posts, configs), always compare old vs new. Verify new version is LONGER and has MORE detail, not less. "ADD, NEVER REMOVE." If user says "bring back" or "more detail" — you stripped content; fix immediately.

**For content/promotion work (SakSit domain):**
- Audit the plan for risks: expired credentials, platform blocks, karma gates, content rules, account limitations
- Check each deliverable against the zero-cost constraint
- Verify all links, usernames, handles are correct — never invent account names
- Check tone consistency — especially for story-driven content (origin story should be hopeful, not trauma-focused)
- Ensure MH resources (Pieta 1800 247 247, Samaritans 116 123) are included on recovery-related content
- Verify draft assets (images, files) exist before promising to publish

## Then

Advance with `sakthai cycle next` to move to the next stage (joy).
