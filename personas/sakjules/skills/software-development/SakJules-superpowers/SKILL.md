---
name: SakJules-superpowers
description: "Superpowers development methodology: plan execution, subagent-driven-development, and programmatic verification (TDD)."
version: 1.0.0
author: SakJules
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, execution, subagents, teamwork, verification, tdd]
    related_skills: [SakJules-plan, SakJules-test-driven-development, SakJules-requesting-code-review]
---

# Superpowers Workflow

Use this skill when executing complex multi-step features or implementing an existing `PLAN.md` or `.hermes/plans/*.md` file.

## 1. Core Strategies

### A. Subagent-Driven Development (Recommended)
Use this strategy for highly interactive, task-by-task execution where user oversight and feedback are valuable:
1. **Isolate the task**: Take a single bite-sized task from the plan (typically 2-5 minutes of work).
2. **Spawn a subagent**: Use the `invoke_subagent` tool with the `self` model to run the specific task in a clean branch or inherit context.
3. **Task Prompt**: Write a precise task description including target file paths, expected changes, and verification commands.
4. **Review**: Once the subagent reports completion, verify the output (tests, diff, linter) before marking the task complete in `PLAN.md`.

### B. Plan Execution (Batch)
Use this strategy for highly autonomous execution of a sequential task plan:
1. **State Tracking**: Keep track of progress directly in `PLAN.md` using the checkboxes (`- [ ]` -> `- [/]` -> `- [x] YYYY-MM-DD`).
2. **Batch Run**: Sequentially execute the tasks, running tests and verification commands after every code edit.
3. **Commit often**: Make a clean git commit after each task passes verification.

## 2. Objective Verification & TDD
Never rely on self-certification. You must prove code correctness:
1. **Write/Update Tests First**: When implementing or fixing code, add or modify a test in `tests/` that reproduces the behavior/failure.
2. **Run and Verify Failure**: Execute the test command and verify it fails as expected.
3. **Implement Fix**: Write the minimal code required to pass the test.
4. **Run and Verify Pass**: Confirm the test suite runs and passes cleanly.
5. **Run Lint and Security Checks**: Execute Ruff formatting and Bandit security scans to ensure codebase hygiene before committing.

## 3. Progress Logging
Always record technical takeaways in the appropriate Jules journal:
- **SQL / DB optimizations**: Record in `.jules/bolt.md`.
- **UI / UX improvements**: Record in `.jules/palette.md`.
- **Security / Secrets / Safety**: Record in `.jules/sentinel.md`.
