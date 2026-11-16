---
name: sakthai-safety-secrets
category: safety
description: Never capture secrets into memory.
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

# sakthai-safety-secrets

Memory is plaintext SQLite. Do not `learn` API keys, tokens, passwords, or other secrets. If the user pastes one, decline to store it and point them at environment variables (.env) instead.
