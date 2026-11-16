---
name: sakthai-memory-store
category: memory
description: Write durable memory through the one store seam, choosing the right shape.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - memory
    related_skills:
      - sakthai-memory-recall
      - sakthai-memory-search
      - sakthai-learning-curation
---

# sakthai-memory-store

Everything durable goes through one seam — the `learn` tool / `sakthai learn`, never a side file. Pick the shape deliberately:

- **Fact** — something the user told you or an explicit, stable detail. Set `kind` (`note`/`pref`/`project`) and an optional `key` so it is findable later. Facts are authoritative.
- **Observation** — something *you* concluded. It carries a confidence weight and is treated as a prior, not a truth.

Write a fact only when it is worth recalling in a future session; skip transient conversational detail. Reuse a `key` to update rather than pile up near-duplicates — let consolidation and dedupe (see `sakthai-learning-curation`) keep the store clean instead of writing redundant entries.
