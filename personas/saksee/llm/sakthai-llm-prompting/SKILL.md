---
name: sakthai-llm-prompting
category: llm
description: Inject memory, then keep prompts lean.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - llm
    related_skills:
      - sakthai-personal
---

# sakthai-llm-prompting

The system prompt already carries the memory block via `render_prompt_block()`. Don't restate known facts in the task; give the model the goal and let it `recall`/`search` for the rest. Prefer tools over long preambles.
