---
name: sakthai-llm-providers
category: llm
description: Pick the provider deliberately.
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

# sakthai-llm-providers

`run_agent` auto-detects anthropic vs google from the model name and available credentials; override with `--provider`. Default to the latest capable Claude model. Both providers share one tool registry, so behaviour stays consistent.
