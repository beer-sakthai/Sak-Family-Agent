---
name: SakJules-cycle-trust
category: cycle
description: Verify the shipped work is safe to rely on.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - cycle
      - trust
    related_skills:
      - SakJules-cycle-growth
---

# sakthai-cycle-trust

Stage 5 of 6 in the Sak Family cycle — **Trust**. See [Trust.md](../../../../docs/cycle/Trust.md)
for the full guidance and [SOUL.md](../../../../docs/SOUL.md) for the charge model.

## What to do

Confirm safety invariants: filesystem reads stay sandboxed, shell stays opt-in (SAKTHAI_SHELL_ALLOW), memory stays intact. Run `sakthai doctor` and `sakthai memory healthcheck`.

## Then

Advance with `sakthai cycle next` to move to the next stage (growth).
