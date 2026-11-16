---
name: sakthai-memory-recall
category: memory
description: Recall relevant memory before answering.
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
      - sakthai-personal
---

# sakthai-memory-recall

Before responding to anything that depends on prior context, pull what's known: `sakthai recall "<topic>"` or the `recall` tool. Treat facts as authoritative and observations as priors. Don't ask the user for something memory already holds.
