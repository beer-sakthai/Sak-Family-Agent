---
name: sakthai-coding-codebase-knowledge
category: coding
description: Onboard to a codebase systematically by scanning structure, stack, conventions, and concerns.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - coding
      - research
    related_skills:
      - sakthai-coding-conventions
      - sakthai-agent-planning
---

# sakthai-coding-codebase-knowledge

When onboarding to a codebase or performing repository-level discovery, audit the repository systematically:

1. **Verify Stack**: Check dependencies (e.g. `package.json`, `pyproject.toml`) to identify language, runtime, and framework conventions. Do not assume.
2. **Analyze Structure**: Inspect entry points, module layouts, and path aliases (e.g., TS path aliases).
3. **Audit Conventions & Concerns**: Document formatting/linting rules, test directories, and identify areas of high code churn or tech debt.

Output a structured repository map under `docs/codebase/` containing stack details, entry points, and active conventions only if explicitly requested, ensuring every claim is backed by file evidence.
