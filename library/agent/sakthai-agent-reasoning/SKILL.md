---
name: sakthai-agent-reasoning
category: agent
description: Reason and use tools deliberately inside the agent loop.
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
      - sakthai-agent-planning
      - sakthai-agent-tools
      - sakthai-memory-recall
---

# sakthai-agent-reasoning

Inside `sakthai run`, reason toward the goal one verifiable step at a time rather than guessing the whole answer up front:

- **Recall before acting.** Memory is injected into the system prompt — use it; don't ask for what is already known.
- **Pick the smallest tool that advances the task**, read its result, and let that result shape the next step. Don't fire speculative parallel calls when one observation would redirect the rest.
- **Stop when the goal is met.** Extra iterations cost tokens and risk drift; the loop has a bounded iteration cap for a reason.
- **Surface contradictions** between memory, tool output, and the request instead of silently choosing one.
