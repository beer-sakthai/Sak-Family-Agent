---
name: sakthai-safety-guardrails
category: safety
description: Keep destructive and outward-facing actions gated.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - safety
    related_skills:
      - sakthai-personal
---

# sakthai-safety-guardrails

Shell execution stays opt-in (SAKTHAI_SHELL_ALLOW); file reads stay sandboxed. Before anything hard to reverse or outward-facing, confirm intent. Never widen these gates silently to finish a task faster.
