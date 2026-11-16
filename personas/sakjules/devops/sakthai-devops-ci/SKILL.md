---
name: sakthai-devops-ci
category: devops
description: Keep changes green before they land.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - devops
    related_skills:
      - sakthai-personal
---

# sakthai-devops-ci

Run the full local gate before pushing: `pytest`, `ruff check`, `ruff format --check`, `mypy`, `bandit`. Push to a branch, open a PR, and watch CI with `gh run watch`. Don't merge on red.
