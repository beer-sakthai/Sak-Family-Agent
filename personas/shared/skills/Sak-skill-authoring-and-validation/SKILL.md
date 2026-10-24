---
name: Sak-skill-authoring-and-validation
description: Use when creating or editing a skill in Sak-Family-Agent, especially when choosing ownership, writing SKILL.md frontmatter, validating composition, or preparing a skill pull request.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, authoring, validation, frontmatter, composition, pull request]
    related_skills: [Sak-repository-quality]
---

# Skill Authoring and Validation

## Overview

A repository skill is reusable guidance, not a record of one fix. Use RED-GREEN-REFACTOR: test the failure, write minimal guidance, then re-test.

## Choose the Owner

| Scope | Location | Prefix |
|---|---|---|
| Every Sak Family persona | `personas/shared/skills/<name>/` | `Sak-` |
| One persona | `personas/<persona>/skills/<name>/` | Its prefix, such as `SakThai-` |

The leaf directory must equal the SKILL.md `name`. Names use letters, numbers, and hyphens and are at most 64 characters. Shared skills compose into every persona; an overlay wins on collision. Resolve ownership and name/path overlap before editing.

## RED-GREEN-REFACTOR

1. **RED:** In a new context, run a pressure scenario without the proposed skill. Record the prompt, choices, omissions, and rationalizations; combine urgency, sunk cost, authority, or exhaustion for discipline guidance.
2. **GREEN:** Add only guidance addressing those failures. Use a recipe for output-shape problems; reserve prohibitions, rationalization tables, and red flags for discipline failures.
3. **REFACTOR:** Run the scenario with the skill. Record results, add loophole counters, and repeat until two runs are stable. Reading the document is not a test.

## Frontmatter and Content

Use YAML frontmatter with `name` and `description`. Start the description with `Use when...` and describe triggers, not workflow. Add searchable terms, an overview, useful quick reference, common mistakes, and “when not to use” guidance when needed. Put heavy references or reusable tools in separate files.

## Validation

From the repository root, run:

```bash
uv run sakthai skills validate --source library
uv run sakthai skills validate --naming
make compose-personas
uv run pytest tests/test_skills.py -q
git diff --check
```

Inspect intended composed trees, remove generated `build/`, check `git status`, and review staged files with `git diff --cached`. Run broader gates required by the change; core Python changes follow `AGENTS.md`.

## Common Mistakes

- Drafting before RED: delete the draft and start over.
- Wrong owner, prefix, or collision: resolve ownership and match conventions.
- Optional metadata treated as required: follow the native validator.
- Unrun validation or CI claimed as passed: report actual results only.
- Generated output committed: remove `build/` before staging.
- Duplicate PR opened: search open PRs and skill names/paths twice.

## Pull Request Handoff

Fetch and rebase onto latest `origin/main`, repeat the overlap check, inspect branch protection for required checks, and open one focused PR. Begin its description with `SakJules · Master of Automation & CI/CD.`; include scope, motivation, exact results, and deferred risks. Re-run affected checks after rebase. Merge only after required checks are green through the protected PR flow.

## When Not to Use

Do not use this skill for one-off instructions, mechanical rules better enforced by validators, or changes that do not create or edit a repository skill.
