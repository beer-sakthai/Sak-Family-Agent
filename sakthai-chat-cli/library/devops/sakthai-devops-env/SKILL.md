---
name: sakthai-devops-env
category: devops
description: Treat configuration as code, secrets as environment.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - devops
    related_skills:
      - sakthai-personal
---

# sakthai-devops-env

Read paths and settings through `sakthai/config.py`, never hard-code them. Keep secrets in `.env` / environment variables, out of the repo and out of memory. Seed new setups from `.env.example`.
