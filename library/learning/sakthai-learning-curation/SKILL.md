---
name: sakthai-learning-curation
category: learning
description: Keep memory healthy over time — consolidate, dedupe, and forget stale facts.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - learning
    related_skills:
      - sakthai-memory-store
      - sakthai-memory-recall
      - sakthai-learning-patterns
---

# sakthai-learning-curation

Memory is only useful while it stays clean. Curate it as a habit, not a one-off:

- **Consolidate** related entries (`sakthai memory consolidate`) so a topic is one good fact, not five fragments.
- **Deduplicate** (`sakthai memory deduplicate`) after bursts of capture; prefer updating an existing `key` over adding a near-twin.
- **Forget what's wrong or stale** (`forget <id>`) — an outdated preference is worse than no fact, because it is trusted as authoritative.
- **Promote durable observations to facts** once they've held up, and let low-confidence observations age out rather than hardening guesses into truth.

Back up before large mutations (`sakthai memory backup`); the store is the shared seam for every runtime.
