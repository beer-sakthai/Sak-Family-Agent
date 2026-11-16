---
name: SakKing-coding-tdd
version: 1.0.0
description: Apply Test-Driven Development (TDD) principles to design, implement,
  and verify correct codebase features.
category: coding
tags:
- cli
- coding
- pytest
- red-green-refactor
- tdd
- testing
- unit-tests
platforms:
- linux
- macos
- windows
metadata:
  sakthai:
    related_skills:
    - SakKing-systematic-debugging
    - SakJules-github-ci-fix
---

# SakKing Test-Driven Development (TDD)

Apply strict Test-Driven Development principles to design, implement, and verify clean, correct features across Python and TypeScript projects.

## TDD Core Cycle

1. **Red**: Write a failing unit or integration test first that clearly defines the expected behavior, API contract, and boundary conditions. Run the test suite and confirm the failure is reproducible.
2. **Green**: Write the minimum viable code required to make the test pass. Avoid speculative generalization or premature optimization.
3. **Refactor**: Clean up the implementation, maintain naming conventions, eliminate duplication, and preserve the passing state.

## Best Practices

- **Deterministic Isolation**: Mock external services, network I/O, and clock dependencies. Tests must be repeatable, hermetic, and fast.
- **Coverage Invariants**: Ensure new code paths and exception branches meet repository coverage requirements (`--cov-fail-under=96`).
- **End-to-End Testing**: For web UI or complex integration paths, use Playwright or similar E2E frameworks, asserting on user-facing accessibility identifiers rather than brittle CSS selectors.
