---
name: SakSee-cycle-care
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
      - SakSee-cycle-joy
---

# sakthai-cycle-care

Stage 3 of 6 in the Sak Family cycle — **Care**. See [Care.md](../../../../docs/cycle/Care.md)
for the full guidance and [SOUL.md](../../../../docs/SOUL.md) for the charge model.

## What to do

Quality gate: review code, run `pytest`, `ruff`, `mypy`, and `bandit`. Fix root causes, not symptoms. Record lessons with `sakthai learn --kind note --tag lesson` so future Hope stages don't repeat them.

## Then

Advance with `sakthai cycle next` to move to the next stage (joy).
