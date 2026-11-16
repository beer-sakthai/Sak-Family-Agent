---
name: sakthai-agent-tools
category: agent
description: Use the built-in tools deliberately.
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

# sakthai-agent-tools

Prefer doing over asking: read files with `read_file` (sandboxed), run commands with `run_command` (opt-in via SAKTHAI_SHELL_ALLOW), and capture durable facts with `learn`. Report tool failures plainly instead of guessing.
