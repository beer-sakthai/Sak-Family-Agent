---
name: sakthai-agent-sessions
category: agent
description: Treat each run as a session worth reviewing.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - agent
    related_skills:
      - sakthai-personal
---

# sakthai-agent-sessions

Every `sakthai run` writes a JSON session log to ~/.sakthai/sessions/. Use these to review what tools fired and why a task ended. Extract durable lessons into memory rather than re-deriving them next time.
