---
name: SakSee-systematic-debugging
description: 4-phase root cause debugging: understand bugs before fixing.
category: software-development
tags: [debugging, troubleshooting]
---

# Systematic Debugging

## 4 Phases

1. **Understand** — reproduce the bug, gather error messages, understand expected vs actual behavior
2. **Isolate** — narrow down the root cause using binary search / logs /reproducers
3. **Fix** — apply the minimal fix that addresses the root cause
4. **Verify** — the bug is gone and no regressions introduced

## Principles

- Always reproduce first
- One variable at a time
- `git bisect` for regression bugs
- Document root cause and fix in the commit message
