---
name: spec-kit
description: Specification-Driven Development (SDD) using GitHub Spec-Kit. Use when asked to create specifications, feature plans, task breakdowns, project constitutions, or execute spec-driven development.
---

# Spec-Kit (Specification-Driven Development)

Use this skill to guide feature development through executable specifications before writing code.

## Core SDD Workflow Commands

1. **`specify init <dir>`**: Initialize a project with Spec-Kit.
   ```bash
   specify init . --integration opencode
   ```
2. **`/speckit.constitution`**: Establish project principles and technical rules in `.specify/memory/constitution.md`.
3. **`/speckit.specify`**: Describe feature requirements (the *what* and *why*).
4. **`/speckit.plan`**: Define technical architecture, tech stack, and database design.
5. **`/speckit.tasks`**: Generate atomic implementation tasks.
6. **`/speckit.implement`**: Execute tasks deterministically with TDD cycles.
