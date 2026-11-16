---
name: sakthai-devops-github-workflows
category: devops
description: Coordinate codebase changes using GitHub flow, clean PRs, issue updates, and review workflows.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - devops
      - coding
    related_skills:
      - sakthai-devops-ci
      - sakthai-devops-env
---

# sakthai-devops-github-workflows

Integrate changes with remote repositories following standard GitHub flow:

1. **Create Branches**: Use short, descriptive branch prefixes (e.g., `feat/`, `fix/`, `docs/`) branching from `main`.
2. **Atomic Commits**: Keep commits focused on a single change. Write clear, imperative commit messages describing *what* changed and *why*.
3. **PR and Issue Management**: Automatically reference issues (e.g., `closes #123`) in PR descriptions. Before requesting review, verify that local lint, format, type-check, and unit test suites are green.
