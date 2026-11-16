---
name: sakthai-observability-sessions
category: observability
description: Use session logs to debug runs.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - observability
    related_skills:
      - sakthai-personal
---

# sakthai-observability-sessions

Each run writes a JSON log to ~/.sakthai/sessions/ with the task, model, messages, and tool calls. Inspect these to see why a task stopped or which tool erred, instead of re-running blindly.
