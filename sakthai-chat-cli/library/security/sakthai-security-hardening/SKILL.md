---
name: sakthai-security-hardening
category: security
description: Harden the code and runtime; keep privilege least.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - security
    related_skills:
      - sakthai-personal
---

# sakthai-security-hardening

At the Trust stage and before any release: run `bandit`, review dependencies, keep subprocess use shell-free and arg-listed, and keep `run_command` opt-in. Justify every nosec. Prefer the narrowest permission that works.
