---
name: SakJules-coverage-guardian
version: 1.0.0
description: "Enforce strict pytest branch coverage floor (>=96%), detect untested conditional paths, and scaffold deterministic unit tests before PR submission."
category: devops
tags:
- automation
- coverage
- pytest
- quality
- tdd
---

# Coverage Guardian (Pytest >=96% Floor)

Use this skill when developing new features, modifying core package modules (`personas/sakthai/`), or fixing bugs to ensure repository test coverage never drops below the strict 96.0% CI floor.

## Goal

Guard the core package test suite so that:
1. Every code change is verified by automated pytest unit tests.
2. Both statement coverage and **branch coverage** (`--cov-branch`) exceed the 96% ceiling (current suite baseline: ~96.6%).
3. Missing conditional paths (untested `if/else`, early returns, exception blocks) are surfaced and closed before submitting a pull request.

## Prerequisites

- Python 3.11+ / `uv`
- `pytest`, `pytest-cov`, `hypothesis`

## Workflow

### 1. Check Current Repository Coverage

Run the quick full coverage check:
```bash
uv run pytest tests/ -q --cov=sakthai --cov-branch --cov-fail-under=96
```

### 2. Isolate Coverage on Changed Modules

When editing a specific file, measure line and branch coverage locally with missing-line reporting:
```bash
uv run pytest tests/<matching_test>.py --cov=sakthai.<subpackage>.<module> --cov-branch --cov-report=term-missing
```

Look at the `Missing` column:
- `45-48`: Unexecuted lines 45 through 48.
- `52->56`: Uncovered branch transition (e.g., the `if` was True, but never False).

### 3. Scaffold Targeted Tests (TDD Discipline)

Follow the Red-Green-Refactor cycle:
1. **Red**: Add a test case targeting the uncovered branch condition or edge case (e.g., malformed input, network error, empty set).
2. **Green**: Run the test to confirm it executes the uncovered lines and passes.
3. **Refactor**: Clean up test fixtures and ensure assertions are deterministic and mock external dependencies cleanly.

### 4. CI Enforced Exclusions

Review `pyproject.toml` `[tool.coverage.run]` for canonical omissions:
- `*/telegram/bot.py` (early-stage prototype)
- `*/tests/*` (test infrastructure)
- `*/skills/*` (documentation & prompt files)
- `*/evolution/*` (evolution subpackage)
- `*/generate_report.py`

Do not add new omissions without explicit maintainer approval; always prefer adding unit tests.
