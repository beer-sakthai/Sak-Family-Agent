---
name: sakthai-cycle-care
category: cycle
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
      - sakthai-cycle-joy
---

# sakthai-cycle-care

Stage 3 of 6 in the SakThai cycle — **Care**. See [Care.md](../../docs/cycle/Care.md)
for the full guidance and [SOUL.md](../../SOUL.md) for the charge model.

## What to do

Quality gate: review code, run `pytest`, `ruff`, `mypy`, and `bandit`. Fix root causes, not symptoms. Record lessons with `sakthai learn --kind lesson` so future Hope stages don't repeat them.

## Then

Advance with `sakthai cycle next` to move to the next stage (joy).
